"""Historical baseline unit tests.

Validate that the same-weekday-same-hour query produces usable stats
and that deviation scoring correctly flags anomalies.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.services import historical_baseline as hb


class TestDeviation:
    def test_normal_within_one_sigma(self):
        base = hb.BaselineStats(
            samples=50,
            mean_risk=0.3, std_risk=0.1,
            mean_count=20, std_count=5,
            mean_density=0.5, std_density=0.1,
        )
        out = hb.deviation_vs_baseline(
            current_risk=0.32, current_count=21, current_density=0.52,
            baseline=base,
        )
        assert out['anomaly'] == 'normal'
        assert abs(out['z_risk']) < 1.0

    def test_severe_at_three_sigma(self):
        base = hb.BaselineStats(
            samples=50,
            mean_risk=0.3, std_risk=0.1,
            mean_count=20, std_count=5,
            mean_density=0.5, std_density=0.1,
        )
        out = hb.deviation_vs_baseline(
            current_risk=0.7, current_count=20, current_density=0.5,
            baseline=base,
        )
        assert out['anomaly'] == 'severe'
        assert out['z_risk'] >= 3.0

    def test_zero_std_safe_no_divide(self):
        base = hb.BaselineStats(
            samples=50,
            mean_risk=0.3, std_risk=0.0,
            mean_count=20, std_count=0.0,
            mean_density=0.5, std_density=0.0,
        )
        out = hb.deviation_vs_baseline(
            current_risk=0.3, current_count=20, current_density=0.5,
            baseline=base,
        )
        assert out['anomaly'] == 'normal'
        assert out['z_risk'] == 0.0


@pytest.mark.integration
class TestBaselineForCamera:
    def test_insufficient_history_returns_none(self, app, camera):
        from backend.extensions import db
        from backend.models.metric import Metric

        with app.app_context():
            Metric.query.filter_by(camera_id=camera.id).delete()
            db.session.commit()
            out = hb.baseline_for_camera(camera.id)
        assert out is None

    def test_sufficient_history_returns_stats(self, app, camera):
        from backend.extensions import db
        from backend.models.metric import Metric

        ref = datetime.now(timezone.utc)

        with app.app_context():
            Metric.query.filter_by(camera_id=camera.id).delete()
            db.session.commit()

            # Seed 15 samples all aligned to same weekday + hour,
            # spread across past 4 weeks (one per day at that hour).
            base_ts = ref.replace(minute=0, second=0, microsecond=0)
            for i in range(15):
                ts = base_ts - timedelta(weeks=1 + i % 4, minutes=i * 2)
                db.session.add(Metric(
                    camera_id=camera.id,
                    timestamp=ts,
                    risk_score=0.3 + 0.01 * i,
                    count=20 + i,
                    density=0.5,
                ))
            db.session.commit()

            out = hb.baseline_for_camera(camera.id, reference_time=ref)

        assert out is not None
        assert out.samples >= 10
        assert 0.2 < out.mean_risk < 0.6
