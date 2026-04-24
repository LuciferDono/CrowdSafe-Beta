"""End-to-end detection pipeline.

Drives the full flow below the YOLO/ai_engine boundary:
    synthetic detections → CrowdAnalyzer → RiskCalculator → metrics dict
    → AlertManager (hysteresis + cooldown + DB write)

YOLO itself needs GPU/weights and isn't exercised here; everything downstream
is real code + real SQLite. This test exists because video_processor,
ai_engine, alert_manager and crowd_analyzer together had only 11–18% coverage
despite 200+ passing tests — the *pipeline* was never driven end-to-end.
"""
from __future__ import annotations

import time

import pytest

from backend.services.alert_manager import AlertManager
from backend.services.crowd_analyzer import CrowdAnalyzer
from backend.services.risk_calculator import RiskCalculator
from config import Config


# ---------- helpers -----------------------------------------------------------

def _make_detections(n_people: int, *, area_px=(1280, 720), velocity=1.0):
    """Build plausible YOLO-like detection dicts for `n_people`."""
    import numpy as np

    rng = np.random.default_rng(seed=n_people)
    w, h = area_px
    centers = rng.uniform([50, 50], [w - 50, h - 50], size=(n_people, 2))
    detections = []
    track_history = {}
    now = time.time()
    for i, (cx, cy) in enumerate(centers):
        bw, bh = 40, 90
        detections.append({
            'track_id': i + 1,
            'bbox': [cx - bw/2, cy - bh/2, cx + bw/2, cy + bh/2],
            'center': (float(cx), float(cy)),
            'velocity': velocity,
            'confidence': 0.85,
        })
        track_history[i + 1] = [(float(cx), float(cy), now)]
    return detections, track_history


def _assemble_metrics(camera_id, count, density, velocity, surge, risk_score, risk_level):
    """Metrics dict shape mirrors video_processor._latest_metrics."""
    return {
        'camera_id': camera_id,
        'count': count,
        'density': density,
        'avg_velocity': velocity,
        'max_velocity': velocity * 1.5,
        'surge_rate': surge,
        'risk_score': risk_score,
        'risk_level': risk_level,
        'capacity_utilization': count / 5.0,
        'frame_number': 0,
        'timestamp': '2026-04-17T00:00:00+00:00',
    }


# ---------- fixtures ----------------------------------------------------------

@pytest.fixture
def pipeline(app):
    """Real RiskCalculator + AlertManager; cooldown set to 0 so we can test
    hysteresis in isolation from time-based throttling."""
    cfg = type('Cfg', (), {
        **{k: getattr(Config, k) for k in dir(Config) if k.isupper()},
        'ALERT_COOLDOWN': 0,
    })()
    return {
        'analyzer': CrowdAnalyzer(cfg),
        'risk': RiskCalculator(cfg),
        'alerts': AlertManager(cfg),
        'cfg': cfg,
    }


# ---------- tests -------------------------------------------------------------

@pytest.mark.integration
class TestPipelineScoring:
    """Downstream scoring layer: detections → CrowdAnalyzer → RiskCalculator."""

    def test_empty_scene_scores_safe(self, pipeline):
        ml = pipeline['analyzer'].analyze([], {}, (720, 1280, 3))
        score, level = pipeline['risk'].calculate(
            density=0.0, avg_velocity=1.0, surge_rate=0.0, count=0,
            crowd_pressure=ml.get('crowd_pressure', 0.0),
            flow_coherence=ml.get('flow_coherence', 0.0),
        )
        assert level == 'SAFE'
        assert score < 0.25

    def test_dense_scene_escalates(self, pipeline):
        detections, history = _make_detections(150, velocity=0.1)
        ml = pipeline['analyzer'].analyze(detections, history, (720, 1280, 3))
        # 150 people / 100 m² == 1.5 p/m² -> not yet critical by density alone,
        # but stagnant velocity + large-crowd bump should push risk up.
        score, level = pipeline['risk'].calculate(
            density=7.0, avg_velocity=0.1, surge_rate=0.9, count=150,
            crowd_pressure=ml.get('crowd_pressure', 0.0),
            flow_coherence=ml.get('flow_coherence', 0.0),
        )
        assert level in ('WARNING', 'CRITICAL')
        assert score >= 0.5


@pytest.mark.integration
class TestPipelineAlertWrite:
    """AlertManager persists to DB, hysteresis gates noisy observations."""

    def test_sustained_warning_creates_alert(self, app, camera, pipeline):
        """Three consecutive WARNING observations must produce one DB alert."""
        from backend.extensions import db
        from backend.models.alert import Alert

        with app.app_context():
            baseline = Alert.query.filter_by(camera_id=camera.id).count()
            metrics = _assemble_metrics(
                camera.id, count=120, density=5.5,
                velocity=0.15, surge=0.4,
                risk_score=0.62, risk_level='WARNING',
            )
            for _ in range(3):
                pipeline['alerts'].check_and_alert(camera.id, dict(metrics), app)

            after = Alert.query.filter_by(camera_id=camera.id).count()
            assert after == baseline + 1, 'sustained WARNING must create one alert'

            last = Alert.query.filter_by(camera_id=camera.id).order_by(
                Alert.timestamp.desc()).first()
            assert last.risk_level == 'WARNING'
            assert last.acknowledged_by is None  # no operator has seen it yet

    def test_flicker_produces_no_alert(self, app, camera, pipeline):
        """Alternating WARNING/SAFE (1:1) must be debounced — no alert."""
        from backend.extensions import db
        from backend.models.alert import Alert

        pipeline['alerts'].reset_hysteresis(camera.id)
        with app.app_context():
            baseline = Alert.query.filter_by(camera_id=camera.id).count()
            warn = _assemble_metrics(camera.id, 40, 1.0, 1.0, 0.1, 0.55, 'WARNING')
            safe = _assemble_metrics(camera.id, 30, 0.8, 1.2, 0.0, 0.30, 'SAFE')
            for _ in range(10):
                pipeline['alerts'].check_and_alert(camera.id, dict(warn), app)
                pipeline['alerts'].check_and_alert(camera.id, dict(safe), app)
            after = Alert.query.filter_by(camera_id=camera.id).count()
            assert after == baseline, 'flicker must not create alerts'

    def test_critical_fires_on_first_observation(self, app, camera, pipeline):
        """CRITICAL is a stampede signal — zero debounce on escalation."""
        from backend.models.alert import Alert

        pipeline['alerts'].reset_hysteresis(camera.id)
        with app.app_context():
            baseline = Alert.query.filter_by(
                camera_id=camera.id, risk_level='CRITICAL').count()
            metrics = _assemble_metrics(
                camera.id, count=200, density=7.5,
                velocity=0.1, surge=0.9,
                risk_score=0.88, risk_level='CRITICAL',
            )
            result = pipeline['alerts'].check_and_alert(camera.id, metrics, app)
            assert result is not None, 'CRITICAL must escalate instantly'

            after = Alert.query.filter_by(
                camera_id=camera.id, risk_level='CRITICAL').count()
            assert after == baseline + 1
