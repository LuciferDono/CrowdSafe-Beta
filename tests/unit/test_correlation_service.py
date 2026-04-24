"""Correlation service unit tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from backend.services import correlation_service as cs


class TestBestLagCorrelation:
    def test_synchronous_signals(self):
        a = np.sin(np.linspace(0, 6, 60))
        b = a.copy()
        corr, lag = cs._best_lag_correlation(a, b, max_lag_steps=10)
        assert corr > 0.95
        assert lag == 0

    def test_a_leads_b_by_five(self):
        t = np.linspace(0, 6, 60)
        a = np.sin(t)
        b = np.roll(a, 5)
        corr, lag = cs._best_lag_correlation(a, b, max_lag_steps=10)
        assert corr > 0.9
        # Smooth sinusoid → peak may resolve to 4 or 5; must be positive.
        assert lag in {4, 5}

    def test_flat_series_returns_zero(self):
        a = np.full(30, 0.5)
        b = np.random.random(30)
        corr, lag = cs._best_lag_correlation(a, b, max_lag_steps=5)
        assert corr == 0.0
        assert lag == 0


class TestHaversine:
    def test_same_point_zero(self):
        d = cs._haversine_m(12.9, 77.5, 12.9, 77.5)
        assert d == 0.0

    def test_known_distance(self):
        # Approx 111km between 1 deg of latitude.
        d = cs._haversine_m(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < d < 112_000

    def test_missing_coords_returns_none(self):
        assert cs._haversine_m(None, 0, 0, 0) is None


@pytest.mark.integration
class TestDetectWaves:
    def test_two_correlated_cameras(self, app):
        from backend.extensions import db
        from backend.models.camera import Camera
        from backend.models.metric import Metric
        from tests.conftest import _Ref  # noqa: F401

        now = datetime.now(timezone.utc)
        with app.app_context():
            # Fresh sandbox cams.
            for cid in ('wave-a', 'wave-b'):
                Metric.query.filter_by(camera_id=cid).delete()
                Camera.query.filter_by(id=cid).delete()
            db.session.commit()

            db.session.add_all([
                Camera(id='wave-a', name='Wave A', source_type='file',
                       latitude=12.9, longitude=77.5, is_active=True),
                Camera(id='wave-b', name='Wave B', source_type='file',
                       latitude=12.901, longitude=77.5, is_active=True),
            ])

            # 60 samples, one every 5s, B lags A by ~10s.
            for i in range(60):
                risk_a = 0.3 + 0.4 * np.sin(i * 0.3)
                risk_b = 0.3 + 0.4 * np.sin((i - 2) * 0.3)
                ts = now - timedelta(seconds=(60 - i) * 5)
                db.session.add(Metric(
                    camera_id='wave-a', timestamp=ts,
                    risk_score=float(risk_a), density=1.0, count=10,
                ))
                db.session.add(Metric(
                    camera_id='wave-b', timestamp=ts,
                    risk_score=float(risk_b), density=1.0, count=10,
                ))
            db.session.commit()

            result = cs.detect_waves(
                camera_ids=['wave-a', 'wave-b'],
                window_seconds=300,
                step_seconds=5,
                max_lag_seconds=30,
                min_correlation=0.3,
            )

        assert result['status'] == 'ok'
        assert len(result['waves']) >= 1
        top = result['waves'][0]
        assert top['correlation'] > 0.5
        # A leads B → source=wave-a, positive lag.
        assert top['source_camera'] == 'wave-a'
        assert top['target_camera'] == 'wave-b'
        assert top['lag_seconds'] > 0

    def test_insufficient_cameras(self, app):
        result = cs.detect_waves(camera_ids=['nonexistent-cam-xxx'])
        assert result['status'] == 'insufficient_cameras'
        assert result['waves'] == []
