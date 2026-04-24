"""CSRNet dense counter tests.

The actual torch forward pass is mocked — these tests validate the wrapper
contract (decision logic, disabled-by-default, graceful degradation, result
shape) without pulling torch into the unit suite.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from backend.services import dense_counter as dc


class TestShouldUseDense:
    def test_never_mode_always_false(self):
        assert dc.should_use_dense(999, 'never') is False

    def test_always_mode_always_true(self):
        assert dc.should_use_dense(0, 'always') is True

    def test_auto_below_threshold_false(self, monkeypatch):
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_THRESHOLD', 40)
        assert dc.should_use_dense(10, 'auto') is False

    def test_auto_at_threshold_true(self, monkeypatch):
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_THRESHOLD', 40)
        assert dc.should_use_dense(40, 'auto') is True

    def test_auto_above_threshold_true(self, monkeypatch):
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_THRESHOLD', 40)
        assert dc.should_use_dense(200, 'auto') is True


class TestGetSingleton:
    def setup_method(self):
        dc.DenseCounter.reset()

    def teardown_method(self):
        dc.DenseCounter.reset()

    def test_returns_none_when_disabled(self, monkeypatch):
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_ENABLED', False)
        assert dc.DenseCounter.get() is None

    def test_returns_none_when_init_fails(self, monkeypatch):
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_ENABLED', True)
        with patch.object(dc.DenseCounter, '_load',
                          side_effect=RuntimeError('no torch')):
            assert dc.DenseCounter.get() is None

    def test_analyze_frame_returns_none_when_disabled(self, monkeypatch):
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_ENABLED', False)
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        assert dc.analyze_frame(frame) is None

    def test_strict_mode_refuses_random_weights(self, monkeypatch):
        """DENSE_COUNT_STRICT=True must reject counters that never loaded
        pretrained weights. Counts from a randomly-initialized CSRNet are
        meaningless and must not reach production metrics."""
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_ENABLED', True)
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_STRICT', True)

        def fake_load(self):
            self._torch = MagicMock()
            self._model = MagicMock()
            self._weights_loaded = False  # simulate no weights file found

        with patch.object(dc.DenseCounter, '_load', fake_load):
            assert dc.DenseCounter.get() is None

    def test_strict_mode_accepts_loaded_weights(self, monkeypatch):
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_ENABLED', True)
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_STRICT', True)

        def fake_load(self):
            self._torch = MagicMock()
            self._model = MagicMock()
            self._weights_loaded = True

        with patch.object(dc.DenseCounter, '_load', fake_load):
            engine = dc.DenseCounter.get()
            assert engine is not None
            assert engine.weights_loaded is True

    def test_non_strict_mode_allows_random_weights(self, monkeypatch):
        """Default behaviour: dev can still run with random init for
        plumbing tests. Only prod (strict=True) locks this down."""
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_ENABLED', True)
        monkeypatch.setattr(dc.Config, 'DENSE_COUNT_STRICT', False)

        def fake_load(self):
            self._torch = MagicMock()
            self._model = MagicMock()
            self._weights_loaded = False

        with patch.object(dc.DenseCounter, '_load', fake_load):
            engine = dc.DenseCounter.get()
            assert engine is not None
            assert engine.weights_loaded is False


class TestAnalyzeWithMockedModel:
    """Exercise the full inference path with a hand-rolled fake torch model.

    The goal is to verify the contract (count = sum of density map, map is
    preserved, backend label is correct) without depending on actual torch
    weights or GPU.
    """
    def setup_method(self):
        dc.DenseCounter.reset()

    def teardown_method(self):
        dc.DenseCounter.reset()

    def _make_fake_engine(self, density_sum: float = 73.4):
        """Build a DenseCounter instance with a stub torch + stub model."""
        engine = dc.DenseCounter.__new__(dc.DenseCounter)
        engine.config = dc.Config
        engine._infer_lock = __import__('threading').Lock()
        engine._last_warning_ts = 0.0
        engine._device = 'cpu'

        # Stub out torch so the internal no_grad + from_numpy/.to path works.
        fake_torch = MagicMock()
        fake_torch.no_grad.return_value.__enter__ = lambda s: None
        fake_torch.no_grad.return_value.__exit__ = lambda s, *a: None

        def from_numpy(arr):
            t = MagicMock()
            t.unsqueeze.return_value = t
            t.to.return_value = t
            return t
        fake_torch.from_numpy.side_effect = from_numpy
        engine._torch = fake_torch

        # Fake density map output: single-channel map summing to density_sum.
        density_map = np.full((1, 30, 40), density_sum / (30 * 40),
                              dtype=np.float32)
        out = MagicMock()
        out.squeeze.return_value.detach.return_value.cpu.return_value.numpy \
            .return_value = density_map[0]
        engine._model = MagicMock(return_value=out)
        return engine

    def test_analyze_returns_csrnet_backend(self):
        engine = self._make_fake_engine(density_sum=42.0)
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        result = engine.analyze(frame)
        assert result.backend == 'csrnet'
        assert result.count == 42
        assert result.density_map is not None
        assert result.processing_time_ms >= 0

    def test_analyze_rounds_count(self):
        engine = self._make_fake_engine(density_sum=73.6)
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        result = engine.analyze(frame)
        assert result.count == 74  # round-half-to-even lands on 74 here

    def test_analyze_clamps_negative_to_zero(self):
        engine = self._make_fake_engine(density_sum=-3.2)
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        result = engine.analyze(frame)
        assert result.count == 0

    def test_analyze_falls_back_on_exception(self):
        engine = self._make_fake_engine()
        engine._model = MagicMock(side_effect=RuntimeError('CUDA OOM'))
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        result = engine.analyze(frame)
        assert result.backend == 'fallback'
        assert result.count == 0
        assert result.density_map is None


class TestPreprocessing:
    def setup_method(self):
        dc.DenseCounter.reset()

    def teardown_method(self):
        dc.DenseCounter.reset()

    def test_clamps_dimensions_to_multiple_of_eight(self):
        """CSRNet has 3 pool layers; H/W must be /8-aligned."""
        engine = dc.DenseCounter.__new__(dc.DenseCounter)
        engine._device = 'cpu'
        engine._torch = MagicMock()
        engine._torch.from_numpy.return_value.unsqueeze.return_value.to \
            .return_value = 'stub-tensor'

        # Feed an odd-shaped frame (103x157) — preprocess must resize to /8.
        frame = np.zeros((103, 157, 3), dtype=np.uint8)
        engine._preprocess(frame)
        # Confirm the numpy array passed to from_numpy has /8-aligned dims.
        arr = engine._torch.from_numpy.call_args[0][0]
        _, h, w = arr.shape  # CHW after transpose
        assert h % 8 == 0
        assert w % 8 == 0
