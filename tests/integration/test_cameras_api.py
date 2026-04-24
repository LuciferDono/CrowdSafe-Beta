"""Cameras API integration tests."""
from __future__ import annotations

import pytest


@pytest.mark.integration
class TestListCameras:
    def test_list_returns_array(self, client, camera):
        r = client.get('/api/cameras')
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert any(c['id'] == camera.id for c in data)


@pytest.mark.integration
class TestCreateCamera:
    def test_create_with_defaults(self, client):
        r = client.post('/api/cameras', json={'name': 'Field Camera'})
        assert r.status_code == 201
        data = r.get_json()
        assert data['id'].startswith('CAM')
        assert data['name'] == 'Field Camera'
        assert data['area_sqm'] == 100.0

    def test_create_sanitizes_name(self, client):
        long_name = 'X' * 500
        r = client.post('/api/cameras', json={'name': long_name})
        assert r.status_code == 201
        data = r.get_json()
        assert len(data['name']) <= 100


@pytest.mark.integration
class TestGetCamera:
    def test_unknown_returns_404(self, client):
        r = client.get('/api/cameras/no-such-camera')
        assert r.status_code == 404

    def test_get_returns_camera_shape(self, client, camera):
        r = client.get(f'/api/cameras/{camera.id}')
        assert r.status_code == 200
        data = r.get_json()
        assert data['id'] == camera.id
        assert 'is_processing' in data


@pytest.mark.integration
class TestUpdateCamera:
    def test_update_name(self, client, camera):
        r = client.put(f'/api/cameras/{camera.id}', json={'name': 'Renamed Cam'})
        assert r.status_code == 200
        assert r.get_json()['name'] == 'Renamed Cam'

    def test_update_unknown_returns_404(self, client):
        r = client.put('/api/cameras/unknown', json={'name': 'x'})
        assert r.status_code == 404


@pytest.mark.integration
class TestDeleteCamera:
    def test_delete_returns_ok(self, client, app):
        import uuid
        from backend.extensions import db
        from backend.models.camera import Camera

        cam_id = f'cam-delete-{uuid.uuid4().hex[:8]}'
        with app.app_context():
            cam = Camera(id=cam_id, name='To Delete', source_type='file')
            db.session.add(cam)
            db.session.commit()

        r = client.delete(f'/api/cameras/{cam_id}')
        assert r.status_code == 200

    def test_delete_unknown_returns_404(self, client):
        r = client.delete('/api/cameras/no-such-cam')
        assert r.status_code == 404


@pytest.mark.integration
class TestTestCamera:
    def test_no_source_returns_error(self, client, camera):
        r = client.post(f'/api/cameras/{camera.id}/test')
        assert r.status_code == 400
        assert r.get_json()['connection_status'] == 'error'
