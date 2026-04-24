"""Forecast service unit tests.

Validate Holt smoothing + risk level mapping + forecast_camera integration
with the real SQLAlchemy-backed Metric model.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from backend.services import forecast_service as fs


class TestHolt:
    def test_empty_series_returns_zeros(self):
        out, resid = fs._holt(np.array([]), steps=3)
        assert out.tolist() == [0.0, 0.0, 0.0]
        assert resid == 0.0

    def test_single_point_extrapolates_flat(self):
        out, resid = fs._holt(np.array([0.42]), steps=5)
        assert out.tolist() == [0.42] * 5
        assert resid == 0.0

    def test_linear_trend_projects_forward(self):
        series = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        out, _ = fs._holt(series, steps=3, alpha=0.8, beta=0.5, phi=1.0)
        # Undamped trend must strictly increase with positive trend.
        assert out[0] > 0.5
        assert out[1] > out[0]
        assert out[2] > out[1]

    def test_damped_trend_slows_down(self):
        series = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        out, _ = fs._holt(series, steps=10, alpha=0.8, beta=0.5, phi=0.8)
        # Damping → deltas should shrink over time.
        deltas = np.diff(out)
        assert deltas[0] > deltas[-1]

    def test_flat_series_predicts_flat(self):
        series = np.array([0.3] * 6)
        out, resid = fs._holt(series, steps=4, alpha=0.5, beta=0.3)
        assert np.allclose(out, 0.3, atol=0.05)
        # No variance in flat series.
        assert resid < 1e-6


class TestRiskLevel:
    def test_safe_below_warning(self):
        assert fs._risk_level(0.0) == 'SAFE'
        assert fs._risk_level(0.49) == 'SAFE'

    def test_warning_at_threshold(self):
        assert fs._risk_level(0.50) == 'WARNING'
        assert fs._risk_level(0.74) == 'WARNING'

    def test_critical_at_threshold(self):
        assert fs._risk_level(0.75) == 'CRITICAL'
        assert fs._risk_level(1.0) == 'CRITICAL'


@pytest.mark.integration
class TestForecastCamera:
    def test_insufficient_history_returns_empty(self, app, camera):
        from backend.extensions import db
        from backend.models.metric import Metric

        with app.app_context():
            Metric.query.filter_by(camera_id=camera.id).delete()
            db.session.commit()
            out = fs.forecast_camera(camera.id)
        assert out['method'] == 'insufficient_history'
        assert out['points'] == []
        assert out['eta_to_critical_sec'] is None

    def test_rising_risk_detects_eta(self, app, camera):
        from backend.extensions import db
        from backend.models.metric import Metric

        now = datetime.now(timezone.utc)
        with app.app_context():
            # Fresh slate.
            Metric.query.filter_by(camera_id=camera.id).delete()
            db.session.commit()

            # Rising risk trajectory: 0.1 → 0.6 over 10 samples, each 5s apart.
            for i, score in enumerate(np.linspace(0.1, 0.6, 10)):
                db.session.add(Metric(
                    camera_id=camera.id,
                    timestamp=now - timedelta(seconds=(10 - i) * 5),
                    count=50 + i * 10,
                    density=1.0 + i * 0.4,
                    risk_score=float(score),
                    risk_level='WARNING' if score >= 0.5 else 'SAFE',
                ))
            db.session.commit()

            out = fs.forecast_camera(camera.id, horizon_seconds=60, step_seconds=5)

        assert out['method'] == 'holt_damped'
        assert len(out['points']) == 12
        assert out['peak_risk'] > 0.5
        # Trend is strongly up → ETA to critical must be set.
        assert out['eta_to_critical_sec'] is not None
        assert 0 < out['eta_to_critical_sec'] <= 60

    def test_flat_risk_never_reaches_critical(self, app, camera):
        from backend.extensions import db
        from backend.models.metric import Metric

        now = datetime.now(timezone.utc)
        with app.app_context():
            Metric.query.filter_by(camera_id=camera.id).delete()
            db.session.commit()
            for i in range(10):
                db.session.add(Metric(
                    camera_id=camera.id,
                    timestamp=now - timedelta(seconds=(10 - i) * 5),
                    count=20,
                    density=0.5,
                    risk_score=0.1,
                    risk_level='SAFE',
                ))
            db.session.commit()
            out = fs.forecast_camera(camera.id, horizon_seconds=60, step_seconds=5)

        assert out['eta_to_critical_sec'] is None
        assert out['peak_risk'] < 0.5
