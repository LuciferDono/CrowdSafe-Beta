"""Metrics API integration tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def seeded_metrics(app, camera):
    """Insert 3 metric rows for the test camera."""
    from backend.extensions import db
    from backend.models.metric import Metric

    with app.app_context():
        Metric.query.filter_by(camera_id=camera.id).delete()
        db.session.commit()

        base = datetime.now(timezone.utc) - timedelta(minutes=10)
        for i in range(3):
            m = Metric(
                camera_id=camera.id,
                timestamp=base + timedelta(minutes=i),
                count=10 + i,
                density=0.5 + i * 0.1,
                avg_velocity=1.0,
                surge_rate=0.0,
                risk_score=0.3 + i * 0.1,
                risk_level='SAFE',
            )
            db.session.add(m)
        db.session.commit()
        return camera.id


@pytest.mark.integration
class TestGetMetrics:
    def test_list_returns_array(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}')
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_limit_applied(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}?limit=1')
        assert r.status_code == 200
        assert len(r.get_json()) == 1

    def test_with_date_range(self, client, seeded_metrics):
        start = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        end = datetime.now(timezone.utc).isoformat()
        r = client.get(f'/api/metrics/{seeded_metrics}?start={start}&end={end}')
        assert r.status_code == 200

    def test_bad_date_silently_ignored(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}?start=not-a-date')
        assert r.status_code == 200


@pytest.mark.integration
class TestCurrentMetrics:
    def test_falls_back_to_db(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}/current')
        assert r.status_code == 200
        body = r.get_json()
        assert body.get('camera_id') == seeded_metrics

    def test_empty_camera_returns_empty(self, client):
        r = client.get('/api/metrics/no-such-cam/current')
        assert r.status_code == 200
        assert r.get_json() == {}


@pytest.mark.integration
class TestSummary:
    def test_shape(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}/summary')
        assert r.status_code == 200
        data = r.get_json()
        for k in ('avg_density', 'peak_count', 'avg_count', 'max_risk_score',
                  'avg_velocity', 'avg_risk', 'max_density', 'total_records'):
            assert k in data
        assert data['total_records'] == 3


@pytest.mark.integration
class TestAggregate:
    def test_hourly_default(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}/aggregate')
        assert r.status_code == 200
        rows = r.get_json()
        assert isinstance(rows, list)
        assert len(rows) >= 1
        assert 'bucket' in rows[0]

    def test_daily(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}/aggregate?interval=daily')
        assert r.status_code == 200

    def test_unknown_interval_falls_back(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}/aggregate?interval=quarterly')
        assert r.status_code == 200


@pytest.mark.integration
class TestGlobalSummary:
    def test_returns_shape(self, client):
        r = client.get('/api/metrics/summary')
        assert r.status_code == 200
        data = r.get_json()
        assert 'total_people' in data
        assert 'cameras_active' in data
        assert 'max_risk_score' in data
        assert 'max_risk_level' in data


@pytest.mark.integration
class TestExport:
    def test_csv(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}/export?format=csv')
        assert r.status_code == 200
        assert 'text/csv' in r.content_type

    def test_md(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}/export?format=md')
        assert r.status_code == 200

    def test_unsupported_format(self, client, seeded_metrics):
        r = client.get(f'/api/metrics/{seeded_metrics}/export?format=xml')
        assert r.status_code == 400
