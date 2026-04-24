"""Forecast API integration tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest


@pytest.mark.integration
class TestForecastEndpoint:
    def test_without_token_returns_401(self, unauth_client, camera):
        r = unauth_client.get(f'/api/forecast/{camera.id}')
        assert r.status_code == 401

    def test_insufficient_history_returns_empty(self, client, app, camera, auth_headers):
        from backend.extensions import db
        from backend.models.metric import Metric

        with app.app_context():
            Metric.query.filter_by(camera_id=camera.id).delete()
            db.session.commit()

        r = client.get(f'/api/forecast/{camera.id}', headers=auth_headers)
        assert r.status_code == 200
        assert r.get_json()['method'] == 'insufficient_history'

    def test_clamps_lookback_seconds(self, client, app, camera, auth_headers):
        from backend.extensions import db
        from backend.models.metric import Metric

        # Seed just enough history to get a real forecast back.
        with app.app_context():
            Metric.query.filter_by(camera_id=camera.id).delete()
            now = datetime.now(timezone.utc)
            for i, score in enumerate(np.linspace(0.1, 0.5, 6)):
                db.session.add(Metric(
                    camera_id=camera.id,
                    timestamp=now - timedelta(seconds=(6 - i) * 5),
                    risk_score=float(score),
                    density=1.0,
                    count=10,
                ))
            db.session.commit()

        r = client.get(
            f'/api/forecast/{camera.id}?lookback_seconds=99999&step_seconds=999',
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data['method'] in {'holt_damped', 'insufficient_history'}
        if data['method'] == 'holt_damped':
            assert data['step_seconds'] <= 60
            assert 'reliability' in data
            assert data['reliability'] in {'high', 'medium', 'low'}

    def test_clamps_horizon_seconds(self, client, app, camera, auth_headers):
        from backend.extensions import db
        from backend.models.metric import Metric

        with app.app_context():
            Metric.query.filter_by(camera_id=camera.id).delete()
            now = datetime.now(timezone.utc)
            for i, score in enumerate(np.linspace(0.1, 0.5, 10)):
                db.session.add(Metric(
                    camera_id=camera.id,
                    timestamp=now - timedelta(seconds=(10 - i) * 5),
                    risk_score=float(score),
                    density=1.0,
                    count=10,
                ))
            db.session.commit()

        # Far-over-cap horizon should be clamped to FORECAST_HORIZON_MAX.
        r = client.get(
            f'/api/forecast/{camera.id}?horizon_seconds=99999',
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.get_json()
        if data['method'] == 'holt_damped':
            assert data['horizon_seconds'] <= 900
            # Confidence band fields present.
            p0 = data['points'][0]
            assert 'risk_lower' in p0 and 'risk_upper' in p0
            assert p0['risk_lower'] <= p0['risk_score'] <= p0['risk_upper']

    def test_long_horizon_returns_300s_default(self, client, app, camera, auth_headers):
        from backend.extensions import db
        from backend.models.metric import Metric

        with app.app_context():
            Metric.query.filter_by(camera_id=camera.id).delete()
            now = datetime.now(timezone.utc)
            # 60 samples over 600s of history.
            for i, score in enumerate(np.linspace(0.2, 0.4, 60)):
                db.session.add(Metric(
                    camera_id=camera.id,
                    timestamp=now - timedelta(seconds=(60 - i) * 10),
                    risk_score=float(score),
                    density=1.0,
                    count=10,
                ))
            db.session.commit()

        r = client.get(
            f'/api/forecast/{camera.id}?step_seconds=10',
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.get_json()
        if data['method'] == 'holt_damped':
            # Default horizon is 300s → 30 points at 10s step.
            assert data['horizon_seconds'] == 300
            assert len(data['points']) == 30
            assert data['points'][-1]['t_plus_sec'] == 300
