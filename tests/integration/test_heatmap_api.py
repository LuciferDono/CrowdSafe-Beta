"""Heatmap API integration tests."""
from __future__ import annotations

import base64
import uuid

import numpy as np
import pytest

from backend.services import heatmap_service as hs


def _seed_cam(app, cam_id):
    from backend.extensions import db
    from backend.models.camera import Camera
    with app.app_context():
        cam = Camera.query.filter_by(id=cam_id).first()
        if cam is None:
            cam = Camera(id=cam_id, name='HeatCam', source_type='file',
                         expected_capacity=500)
            db.session.add(cam)
            db.session.commit()


def _seed_sample(app, cam_id, count=42):
    from backend.extensions import db
    with app.app_context():
        src = np.random.random((32, 32)).astype(np.float32)
        hs.persist_sample(cam_id, src, count)
        db.session.commit()


@pytest.mark.integration
class TestHeatmapEndpoint:
    def test_unknown_camera_returns_404(self, client):
        r = client.get('/api/cameras/nope/heatmap')
        assert r.status_code == 404

    def test_requires_token(self, unauth_client):
        r = unauth_client.get('/api/cameras/any/heatmap')
        assert r.status_code == 401

    def test_empty_camera_returns_empty_samples(self, client, app):
        cam_id = f'heat-{uuid.uuid4().hex[:6]}'
        _seed_cam(app, cam_id)
        r = client.get(f'/api/cameras/{cam_id}/heatmap')
        assert r.status_code == 200
        body = r.get_json()
        assert body['camera_id'] == cam_id
        assert body['samples'] == []

    def test_returns_samples_newest_first(self, client, app):
        cam_id = f'heat-{uuid.uuid4().hex[:6]}'
        _seed_cam(app, cam_id)
        _seed_sample(app, cam_id, count=10)
        _seed_sample(app, cam_id, count=20)

        r = client.get(f'/api/cameras/{cam_id}/heatmap?limit=5')
        assert r.status_code == 200
        samples = r.get_json()['samples']
        assert len(samples) == 2
        # Newest first.
        assert samples[0]['person_count'] == 20
        assert samples[1]['person_count'] == 10

    def test_include_grid_false_omits_grid_data(self, client, app):
        cam_id = f'heat-{uuid.uuid4().hex[:6]}'
        _seed_cam(app, cam_id)
        _seed_sample(app, cam_id)

        r = client.get(f'/api/cameras/{cam_id}/heatmap?include_grid=0')
        samples = r.get_json()['samples']
        assert 'grid_data' not in samples[0]
        assert samples[0]['grid_rows'] == hs.DEFAULT_GRID_ROWS


@pytest.mark.integration
class TestHeatmapCurrent:
    def test_no_samples_returns_404(self, client, app):
        cam_id = f'heat-{uuid.uuid4().hex[:6]}'
        _seed_cam(app, cam_id)
        r = client.get(f'/api/cameras/{cam_id}/heatmap/current')
        assert r.status_code == 404

    def test_returns_latest_decodable_grid(self, client, app):
        cam_id = f'heat-{uuid.uuid4().hex[:6]}'
        _seed_cam(app, cam_id)
        _seed_sample(app, cam_id, count=77)

        r = client.get(f'/api/cameras/{cam_id}/heatmap/current')
        assert r.status_code == 200
        payload = r.get_json()
        assert payload['person_count'] == 77
        # Grid round-trips.
        decoded = hs.decode_grid(
            payload['grid_data'], payload['grid_rows'], payload['grid_cols']
        )
        assert decoded.shape == (payload['grid_rows'], payload['grid_cols'])
