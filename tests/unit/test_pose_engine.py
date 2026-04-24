"""Pose engine heuristic tests.

These validate the pure-geometry helpers in isolation — no YOLO model load
required. The PoseEngine class itself is only instantiable when the YOLO
weights file is present, so we skip those paths here.
"""
from __future__ import annotations

import numpy as np
import pytest

from backend.services import pose_engine as pe


def _kp(points: dict[str, tuple[float, float]], conf: float = 0.9) -> tuple[np.ndarray, np.ndarray]:
    """Build a (17,2) keypoint array + (17,) confidence row from a named dict."""
    xy = np.zeros((17, 2), dtype=float)
    c = np.zeros(17, dtype=float)
    for name, (x, y) in points.items():
        idx = pe._KP[name]
        xy[idx] = (x, y)
        c[idx] = conf
    return xy, c


class TestFallen:
    def test_upright_not_fallen(self):
        xy, c = _kp({'l_shoulder': (100, 100), 'l_hip': (100, 250)})
        assert not pe._is_fallen(xy, c)

    def test_horizontal_body_fallen(self):
        # Shoulder to hip lies along x-axis → angle from vertical ~90°.
        xy, c = _kp({'l_shoulder': (100, 100), 'l_hip': (250, 100)})
        assert pe._is_fallen(xy, c)

    def test_low_confidence_returns_false(self):
        xy, c = _kp({'l_shoulder': (100, 100), 'l_hip': (250, 100)}, conf=0.1)
        assert not pe._is_fallen(xy, c)


class TestCompressed:
    def test_normal_torso_not_compressed(self):
        xy, c = _kp({
            'l_shoulder': (100, 100), 'r_shoulder': (160, 100),
            'l_hip': (100, 260), 'r_hip': (160, 260),
        })
        # torso_len=160, shoulder_width=60 → 160 > 0.6*60 → not compressed.
        assert not pe._is_compressed(xy, c)

    def test_heavy_compression_detected(self):
        xy, c = _kp({
            'l_shoulder': (100, 100), 'r_shoulder': (200, 100),
            'l_hip': (100, 120), 'r_hip': (200, 120),
        })
        # torso_len=20, shoulder_width=100 → 20 < 0.6*100 → compressed.
        assert pe._is_compressed(xy, c)


class TestArmsUp:
    def test_arms_down_not_flagged(self):
        xy, c = _kp({
            'l_shoulder': (100, 100), 'r_shoulder': (160, 100),
            'l_wrist': (90, 200), 'r_wrist': (170, 200),
        })
        assert not pe._is_arms_up(xy, c)

    def test_both_arms_up_flagged(self):
        xy, c = _kp({
            'l_shoulder': (100, 100), 'r_shoulder': (160, 100),
            'l_wrist': (90, 40), 'r_wrist': (170, 40),
        })
        assert pe._is_arms_up(xy, c)

    def test_only_one_arm_up_not_flagged(self):
        xy, c = _kp({
            'l_shoulder': (100, 100), 'r_shoulder': (160, 100),
            'l_wrist': (90, 40), 'r_wrist': (170, 200),
        })
        assert not pe._is_arms_up(xy, c)


class TestCrushRiskBlend:
    def test_zero_persons_zero_risk(self):
        feats = pe.PoseFeatures(n_persons=0)
        assert pe._blend_crush_risk(feats, density=0.0) == 0.0

    def test_fallen_dominates_blend(self):
        feats = pe.PoseFeatures(n_persons=10, n_fallen=5, n_compressed=0, n_arms_up=0)
        risk = pe._blend_crush_risk(feats, density=0.0)
        # 0.6 * 0.5 = 0.3 base; density_mult=1.0 → 0.3.
        assert risk == pytest.approx(0.3, abs=0.01)

    def test_density_amplifies_risk(self):
        feats = pe.PoseFeatures(n_persons=10, n_fallen=5)
        low = pe._blend_crush_risk(feats, density=0.0)
        high = pe._blend_crush_risk(feats, density=6.0)
        assert high > low
        assert high <= 1.0

    def test_clamps_at_one(self):
        feats = pe.PoseFeatures(n_persons=10, n_fallen=10, n_compressed=10, n_arms_up=10)
        assert pe._blend_crush_risk(feats, density=20.0) == 1.0


class TestAnalyzeFrame:
    def test_returns_none_when_pose_disabled(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'POSE_ENABLED', False)
        pe.PoseEngine._instance = None
        assert pe.analyze_frame(np.zeros((1, 1, 3), dtype=np.uint8)) is None
