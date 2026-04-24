"""CSRNet dense crowd counter.

YOLO bbox detection saturates at ~50 people/frame due to occlusion. At the
exact density where stampede risk emerges (stadium ingress, temple ghats,
religious processions), YOLO silently under-counts. CSRNet regresses a
density map directly from pixels — sum of the map is the count — and stays
reliable well beyond 200 people per frame.

Design
------
- Lazy-loaded singleton (same pattern as ``pose_engine``).
- Torch backend. VGG16-frontend + dilated-convolution backend (standard
  CSRNet architecture from Li et al., CVPR 2018).
- Weights fetched once via HuggingFace (``hf_service.download_model``).
  The repo + file are configurable; this module does NOT hardcode a URL.
- If torch, weights, or the model all fail to materialize, the engine
  returns ``None`` gracefully — calling code must handle that.
- Pure inference, no cross-frame state. Safe to call from the processor
  thread; an internal lock serializes torch forward passes.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from config import Config

logger = logging.getLogger('dense_counter')

_INPUT_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_INPUT_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


@dataclass
class DenseCount:
    count: int
    density_map: np.ndarray | None
    processing_time_ms: float
    backend: str  # 'csrnet' | 'fallback'


def _build_csrnet(torch_mod: Any, nn_mod: Any):
    """Return a CSRNet nn.Module. Constructed lazily to avoid torch import
    at module load (pose_engine pattern)."""

    class CSRNet(nn_mod.Module):
        def __init__(self):
            super().__init__()
            self.frontend = nn_mod.Sequential(
                nn_mod.Conv2d(3, 64, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(64, 64, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.MaxPool2d(2, 2),
                nn_mod.Conv2d(64, 128, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(128, 128, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.MaxPool2d(2, 2),
                nn_mod.Conv2d(128, 256, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(256, 256, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(256, 256, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.MaxPool2d(2, 2),
                nn_mod.Conv2d(256, 512, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(512, 512, 3, padding=1), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(512, 512, 3, padding=1), nn_mod.ReLU(inplace=True),
            )
            # Dilated backend — expands receptive field without losing resolution.
            self.backend = nn_mod.Sequential(
                nn_mod.Conv2d(512, 512, 3, padding=2, dilation=2), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(512, 512, 3, padding=2, dilation=2), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(512, 512, 3, padding=2, dilation=2), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(512, 256, 3, padding=2, dilation=2), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(256, 128, 3, padding=2, dilation=2), nn_mod.ReLU(inplace=True),
                nn_mod.Conv2d(128, 64, 3, padding=2, dilation=2), nn_mod.ReLU(inplace=True),
            )
            self.output_layer = nn_mod.Conv2d(64, 1, 1)

        def forward(self, x):
            x = self.frontend(x)
            x = self.backend(x)
            return self.output_layer(x)

    return CSRNet()


class DenseCounter:
    """Lazy CSRNet wrapper. Only instantiate if DENSE_COUNT_ENABLED."""

    _instance: 'DenseCounter | None' = None
    _lock = threading.Lock()

    def __init__(self, config=Config):
        self.config = config
        self._infer_lock = threading.Lock()
        self._last_warning_ts = 0.0
        self._torch = None
        self._model = None
        self._device = 'cpu'
        self._weights_loaded = False
        self._load()

    def _load(self) -> None:
        import torch
        from torch import nn

        self._torch = torch
        self._device = 'cuda' if torch.cuda.is_available() else 'cpu'

        model = _build_csrnet(torch, nn)

        weights_path = self._resolve_weights()
        if weights_path and os.path.exists(weights_path):
            try:
                state = torch.load(weights_path, map_location=self._device)
                if isinstance(state, dict) and 'state_dict' in state:
                    state = state['state_dict']
                # Tolerate common key prefixes (``module.`` from DataParallel).
                stripped = {
                    (k[7:] if k.startswith('module.') else k): v
                    for k, v in state.items()
                }
                model.load_state_dict(stripped, strict=False)
                self._weights_loaded = True
                logger.info('CSRNet weights loaded from %s', weights_path)
            except Exception as e:
                logger.warning(
                    'CSRNet weights failed to load (%s); using random init. '
                    'Counts will be unreliable until real weights are provided.',
                    e,
                )
        else:
            logger.warning(
                'CSRNet running with random weights — set DENSE_COUNT_MODEL_REPO '
                'and DENSE_COUNT_MODEL_FILE to download pretrained weights.'
            )

        model.eval()
        model.to(self._device)
        self._model = model

    @property
    def weights_loaded(self) -> bool:
        return self._weights_loaded

    def _resolve_weights(self) -> str | None:
        repo = getattr(self.config, 'DENSE_COUNT_MODEL_REPO', '') or ''
        filename = getattr(self.config, 'DENSE_COUNT_MODEL_FILE', '') or ''
        if not repo or not filename:
            return None
        try:
            from backend.services.hf_service import download_model
            return download_model(repo, filename=filename)
        except Exception as e:
            logger.warning('CSRNet weight download failed for %s/%s: %s',
                           repo, filename, e)
            return None

    @classmethod
    def get(cls) -> 'DenseCounter | None':
        if not getattr(Config, 'DENSE_COUNT_ENABLED', False):
            return None
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    try:
                        candidate = DenseCounter()
                    except Exception as e:
                        logger.warning('DenseCounter init failed: %s', e)
                        cls._instance = None
                        return None
                    # Strict mode: only hand back the singleton if real
                    # pretrained weights loaded. Random init is silently
                    # catastrophic in production — refuse to serve it.
                    strict = getattr(Config, 'DENSE_COUNT_STRICT', False)
                    if strict and not candidate.weights_loaded:
                        logger.error(
                            'DENSE_COUNT_STRICT=True and CSRNet has no real '
                            'weights — disabling dense counting for this run. '
                            'Set DENSE_COUNT_MODEL_REPO + DENSE_COUNT_MODEL_FILE '
                            'to a valid HuggingFace checkpoint to re-enable.'
                        )
                        cls._instance = None
                        return None
                    cls._instance = candidate
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Test hook: drop the cached singleton."""
        with cls._lock:
            cls._instance = None

    def analyze(self, frame: np.ndarray) -> DenseCount:
        """Run a forward pass on a BGR uint8 frame. Returns integer count
        plus the raw density map (useful for heatmap overlay)."""
        start = time.time()
        try:
            tensor = self._preprocess(frame)
            with self._infer_lock:
                with self._torch.no_grad():
                    out = self._model(tensor)
            density = out.squeeze().detach().cpu().numpy()
            count = int(round(float(density.sum())))
            elapsed = (time.time() - start) * 1000.0
            return DenseCount(
                count=max(0, count),
                density_map=density,
                processing_time_ms=round(elapsed, 2),
                backend='csrnet',
            )
        except Exception as e:
            now = time.time()
            if now - self._last_warning_ts > 60:
                logger.warning('CSRNet inference failed: %s', e)
                self._last_warning_ts = now
            elapsed = (time.time() - start) * 1000.0
            return DenseCount(count=0, density_map=None,
                              processing_time_ms=round(elapsed, 2),
                              backend='fallback')

    def _preprocess(self, frame: np.ndarray):
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        # Clamp to multiple of 8 — CSRNet has 3 pooling layers.
        h, w = rgb.shape[:2]
        nh = max(64, (h // 8) * 8)
        nw = max(64, (w // 8) * 8)
        if (nh, nw) != (h, w):
            rgb = cv2.resize(rgb, (nw, nh))
        rgb = (rgb - _INPUT_MEAN) / _INPUT_STD
        # HWC -> NCHW
        tensor = self._torch.from_numpy(rgb.transpose(2, 0, 1)).unsqueeze(0)
        return tensor.to(self._device)


def analyze_frame(frame: np.ndarray) -> DenseCount | None:
    """Convenience wrapper used by the video pipeline."""
    engine = DenseCounter.get()
    if engine is None:
        return None
    return engine.analyze(frame)


def should_use_dense(yolo_count: int, dense_mode: str = 'auto') -> bool:
    """Decide whether to invoke CSRNet for this frame.

    - ``always``: every frame (expensive; only for validation runs)
    - ``never``:  skip CSRNet entirely
    - ``auto``:   kick in when YOLO count crosses threshold
    """
    if dense_mode == 'never':
        return False
    if dense_mode == 'always':
        return True
    threshold = getattr(Config, 'DENSE_COUNT_THRESHOLD', 40)
    return yolo_count >= threshold
