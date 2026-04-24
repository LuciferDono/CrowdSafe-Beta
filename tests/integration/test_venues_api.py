"""Venue API + aggregation integration tests."""
from __future__ import annotations

import uuid

import pytest


def _seed_venue(app, vid, name='V', cap=500):
    from backend.extensions import db
    from backend.models.venue import Venue

    with app.app_context():
        v = Venue.query.filter_by(id=vid).first()
        if v is None:
            v = Venue(id=vid, name=name, venue_type='stadium',
                      expected_capacity=cap, is_active=True)
            db.session.add(v)
            db.session.commit()


@pytest.mark.integration
class TestVenueCRUD:
    def test_requires_token_for_list(self, unauth_client):
        r = unauth_client.get('/api/venues')
        assert r.status_code == 401

    def test_list_returns_array(self, client):
        r = client.get('/api/venues')
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)

    def test_create_requires_admin(self, client):
        # `client` authenticates as admin via fixture, so this should succeed.
        vid = f'venue-{uuid.uuid4().hex[:6]}'
        r = client.post('/api/venues', json={
            'id': vid, 'name': 'Test Venue', 'venue_type': 'stadium',
            'expected_capacity': 1000,
        })
        assert r.status_code == 201
        assert r.get_json()['id'] == vid

    def test_create_duplicate_returns_409(self, client, app):
        vid = f'venue-dup-{uuid.uuid4().hex[:6]}'
        _seed_venue(app, vid)
        r = client.post('/api/venues', json={'id': vid, 'name': 'dup'})
        assert r.status_code == 409

    def test_update_venue(self, client, app):
        vid = f'venue-upd-{uuid.uuid4().hex[:6]}'
        _seed_venue(app, vid)
        r = client.put(f'/api/venues/{vid}', json={'name': 'renamed'})
        assert r.status_code == 200
        assert r.get_json()['name'] == 'renamed'

    def test_delete_venue(self, client, app):
        vid = f'venue-del-{uuid.uuid4().hex[:6]}'
        _seed_venue(app, vid)
        r = client.delete(f'/api/venues/{vid}')
        assert r.status_code == 200


@pytest.mark.integration
class TestVenueAggregate:
    def test_unknown_venue_returns_404(self, client):
        r = client.get('/api/venues/nope/risk')
        assert r.status_code == 404

    def test_aggregate_combines_cameras(self, client, app):
        from backend.extensions import db
        from backend.models.camera import Camera
        from backend.models.metric import Metric
        from datetime import datetime, timezone

        vid = f'venue-agg-{uuid.uuid4().hex[:6]}'
        _seed_venue(app, vid, cap=1000)

        with app.app_context():
            now = datetime.now(timezone.utc)
            cam_a = Camera(id=f'{vid}-a', name='A', source_type='file',
                           venue_id=vid, expected_capacity=500)
            cam_b = Camera(id=f'{vid}-b', name='B', source_type='file',
                           venue_id=vid, expected_capacity=500)
            db.session.add_all([cam_a, cam_b])
            db.session.add(Metric(
                camera_id=cam_a.id, timestamp=now,
                risk_score=0.8, density=2.5, count=100,
                risk_level='CRITICAL',
            ))
            db.session.add(Metric(
                camera_id=cam_b.id, timestamp=now,
                risk_score=0.3, density=0.5, count=50,
                risk_level='SAFE',
            ))
            db.session.commit()

        r = client.get(f'/api/venues/{vid}/risk')
        assert r.status_code == 200
        data = r.get_json()
        assert data['total_cameras'] == 2
        assert data['active_cameras'] == 2
        assert data['peak_risk'] == 0.8
        assert data['total_count'] == 150
        # Weighted risk: (0.8*100 + 0.3*50) / 150 = 95/150 ≈ 0.633
        assert abs(data['weighted_risk'] - 0.633) < 0.01
        assert data['venue_level'] == 'CRITICAL'
        assert data['utilization'] == 0.15
