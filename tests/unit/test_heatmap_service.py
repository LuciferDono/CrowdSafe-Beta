"""Heatmap service unit tests."""
from __future__ import annotations

import base64
import time

import numpy as np
import pytest

from backend.services import heatmap_service as hs


class TestDownsample:
    def test_none_returns_zeros(self):
        grid = hs.downsample_grid(None, rows=4, cols=4)
        assert grid.shape == (4, 4)
        assert grid.sum() == 0

    def test_empty_returns_zeros(self):
        grid = hs.downsample_grid(np.zeros((0, 0)), rows=4, cols=4)
        assert grid.shape == (4, 4)

    def test_uniform_density_uniform_grid(self):
        src = np.full((32, 32), 0.5, dtype=np.float32)
        grid = hs.downsample_grid(src, rows=4, cols=4)
        # Normalized by max cell → uniform == 1.0 everywhere.
        assert grid.shape == (4, 4)
        assert np.allclose(grid, 1.0)

    def test_peak_preserved_at_hotspot(self):
        src = np.zeros((32, 32), dtype=np.float32)
        src[0:8, 0:8] = 1.0  # Top-left quadrant hot.
        grid = hs.downsample_grid(src, rows=4, cols=4)
        assert grid[0, 0] == 1.0
        assert grid[3, 3] < grid[0, 0]

    def test_tiny_input_uses_fallback(self):
        src = np.array([[0.0, 1.0], [0.5, 0.2]], dtype=np.float32)
        grid = hs.downsample_grid(src, rows=4, cols=4)
        assert grid.shape == (4, 4)


class TestEncodeDecode:
    def test_round_trip_preserves_shape(self):
        src = np.random.random((8, 8)).astype(np.float32)
        encoded = hs.encode_grid(src)
        decoded = hs.decode_grid(encoded, 8, 8)
        assert decoded.shape == (8, 8)

    def test_round_trip_values_close(self):
        src = np.linspace(0, 1, 256, dtype=np.float32).reshape(16, 16)
        encoded = hs.encode_grid(src)
        decoded = hs.decode_grid(encoded, 16, 16)
        assert np.abs(decoded - src).max() < 0.01  # uint8 quant error ≤ 1/255

    def test_encoded_is_base64(self):
        src = np.zeros((4, 4), dtype=np.float32)
        encoded = hs.encode_grid(src)
        # Must be valid base64.
        base64.b64decode(encoded)


class TestSampleRateGate:
    def test_first_call_samples(self):
        gate = hs.SampleRateGate(interval_s=1.0)
        assert gate.should_sample(now=100.0) is True

    def test_too_soon_skips(self):
        gate = hs.SampleRateGate(interval_s=10.0)
        gate.should_sample(now=100.0)
        assert gate.should_sample(now=101.0) is False

    def test_after_interval_samples(self):
        gate = hs.SampleRateGate(interval_s=5.0)
        gate.should_sample(now=100.0)
        assert gate.should_sample(now=106.0) is True
