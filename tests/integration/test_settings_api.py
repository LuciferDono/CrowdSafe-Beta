"""Settings API integration tests."""
from __future__ import annotations

import pytest


@pytest.fixture
def seeded_settings(app):
    """Reset to known values each test — other tests mutate these rows."""
    from backend.extensions import db
    from backend.models.setting import Setting

    with app.app_context():
        for cat, key, val in (
            ('risk', 'critical_threshold', '0.75'),
            ('risk', 'warning_threshold', '0.50'),
            ('video', 'fps_target', '15'),
        ):
            row = Setting.query.filter_by(key=key).first()
            if row is None:
                db.session.add(Setting(key=key, value=val, category=cat))
            else:
                row.value = val
                row.category = cat
        db.session.commit()


@pytest.mark.integration
class TestListSettings:
    def test_returns_grouped(self, client, seeded_settings):
        r = client.get('/api/settings')
        assert r.status_code == 200
        body = r.get_json()
        assert isinstance(body, dict)
        assert 'risk' in body
        assert body['risk']['critical_threshold'] == '0.75'


@pytest.mark.integration
class TestGetCategory:
    def test_known(self, client, seeded_settings):
        r = client.get('/api/settings/risk')
        assert r.status_code == 200
        data = r.get_json()
        assert data['warning_threshold'] == '0.50'

    def test_unknown_returns_empty(self, client):
        r = client.get('/api/settings/no-such-category')
        assert r.status_code == 200
        assert r.get_json() == {}


@pytest.mark.integration
class TestUpdateSetting:
    def test_creates_new(self, client):
        r = client.put('/api/settings/video/fps_cap', json={'value': 20})
        assert r.status_code == 200
        assert r.get_json()['key'] == 'fps_cap'

    def test_updates_existing(self, client, seeded_settings):
        r = client.put('/api/settings/risk/critical_threshold', json={'value': 0.8})
        assert r.status_code == 200
        assert r.get_json()['value'] == '0.8'


@pytest.mark.integration
class TestRiskThresholds:
    def test_bulk_upsert(self, client):
        r = client.post('/api/settings/risk-thresholds', json={
            'caution_threshold': 0.3,
            'warning_threshold': 0.55,
        })
        assert r.status_code == 200
        body = r.get_json()
        assert body['status'] == 'updated'
        assert 'thresholds' in body
