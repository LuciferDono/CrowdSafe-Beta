"""Correlation API integration tests."""
from __future__ import annotations

import pytest


@pytest.mark.integration
class TestCorrelationEndpoint:
    def test_without_token_returns_401(self, unauth_client):
        r = unauth_client.get('/api/correlation/waves')
        assert r.status_code == 401

    def test_with_token_returns_200(self, client):
        r = client.get('/api/correlation/waves?window_seconds=60')
        assert r.status_code == 200
        data = r.get_json()
        assert 'waves' in data
        assert 'status' in data

    def test_accepts_camera_filter(self, client):
        r = client.get('/api/correlation/waves?camera_ids=foo,bar&window_seconds=60')
        assert r.status_code == 200
