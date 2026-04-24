"""Alerts API integration tests."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest


@pytest.fixture
def sample_alert(app, camera):
    from backend.extensions import db
    from backend.models.alert import Alert
    from tests.conftest import _Ref

    alert_id = 'alert-test-001'
    with app.app_context():
        existing = Alert.query.filter_by(alert_id=alert_id).first()
        if existing is None:
            existing = Alert(
                alert_id=alert_id,
                camera_id=camera.id,
                risk_level='CRITICAL',
                trigger_condition='DENSITY_EXCEEDED',
                message='Crowd density exceeded threshold',
                metrics_snapshot='{}',
            )
            db.session.add(existing)
            db.session.commit()
        return _Ref(
            id=existing.id,
            alert_id=existing.alert_id,
            camera_id=existing.camera_id,
            risk_level=existing.risk_level,
        )


@pytest.mark.integration
class TestListAlerts:
    def test_list_returns_array(self, client, sample_alert):
        r = client.get('/api/alerts?limit=1000')
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert any(a['alert_id'] == sample_alert.alert_id for a in data)

    def test_filter_by_camera_id(self, client, sample_alert, camera):
        r = client.get(f'/api/alerts?camera_id={camera.id}')
        assert r.status_code == 200
        for a in r.get_json():
            assert a['camera_id'] == camera.id

    def test_filter_by_risk_level(self, client, sample_alert):
        r = client.get('/api/alerts?risk_level=critical')
        assert r.status_code == 200
        for a in r.get_json():
            assert a['risk_level'] == 'CRITICAL'


@pytest.mark.integration
class TestAcknowledge:
    def test_acknowledge_unknown_returns_404(self, client):
        r = client.post('/api/alerts/does-not-exist/acknowledge')
        assert r.status_code == 404

    def test_acknowledge_flips_flag(self, client, sample_alert):
        r = client.post(f'/api/alerts/{sample_alert.alert_id}/acknowledge')
        assert r.status_code == 200
        body = r.get_json()
        assert body['acknowledged'] is True
        assert body['acknowledged_at'] is not None


@pytest.mark.integration
class TestResolve:
    def test_resolve_also_acknowledges(self, client, app, camera):
        import uuid
        from backend.extensions import db
        from backend.models.alert import Alert

        aid = f'alert-resolve-{uuid.uuid4().hex[:8]}'
        with app.app_context():
            a = Alert(
                alert_id=aid,
                camera_id=camera.id,
                risk_level='WARNING',
                message='x',
            )
            db.session.add(a)
            db.session.commit()

        r = client.post(f'/api/alerts/{aid}/resolve')
        assert r.status_code == 200
        body = r.get_json()
        assert body['resolved'] is True
        assert body['acknowledged'] is True


@pytest.mark.integration
class TestStatistics:
    def test_statistics_shape(self, client, sample_alert):
        r = client.get('/api/alerts/statistics')
        assert r.status_code == 200
        data = r.get_json()
        assert 'total_alerts' in data
        assert 'unresolved' in data
        assert 'by_level' in data
        assert data['total_alerts'] >= 1


@pytest.mark.integration
class TestUnacknowledgedCount:
    def test_returns_count(self, client):
        r = client.get('/api/alerts/unacknowledged/count')
        assert r.status_code == 200
        assert 'count' in r.get_json()


@pytest.mark.integration
class TestIncidentReport:
    def test_missing_report_returns_404(self, client, sample_alert):
        r = client.get(f'/api/alerts/{sample_alert.alert_id}/report')
        assert r.status_code == 404
