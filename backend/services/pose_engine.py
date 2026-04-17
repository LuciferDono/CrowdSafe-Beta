"""YOLO-pose crush / fall / distress detection.

Fuses pose keypoints with the main density/velocity pipeline to raise early
crush signals that bbox-only detection misses:

  - FALLEN:   person body oriented horizontally (shoulder/hip angle > 60°
              from vertical, hip below shoulder)
  - COMPRESSED: shoulder-to-hip torso length < 40% of typical (heavy
              vertical pressure, body folded)
  - ARMS_UP:  both wrists above both shoulders (panic/distress gesture)

Outputs a ``crush_risk`` scalar in [0,1] blended from the counts + density.
Design: pure inference, no state across frames — cheap and idempotent.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field

import numpy as np

from config import Config

logger = logging.getLogger('pose_engine')

# COCO-17 keypoint indices used by Ultralytics YOLO-pose
_KP = {
    'nose': 0,
    'l_shoulder': 5, 'r_shoulder': 6,
    'l_elbow': 7, 'r_elbow': 8,
    'l_wrist': 9, 'r_wrist': 10,
    'l_hip': 11, 'r_hip': 12,
    'l_knee': 13, 'r_knee': 14,
    'l_ankle': 15, 'r_ankle': 16,
}

_KP_CONF_MIN = 0.3


@dataclass
class PoseFeatures:
    n_persons: int = 0
    n_fallen: int = 0
    n_compressed: int = 0
    n_arms_up: int = 0
    crush_risk: float = 0.0
    per_person: list[dict] = field(default_factory=list)


class PoseEngine:
    """Lazy-loaded YOLO-pose wrapper. Only instantiate if POSE_ENABLED."""

    _instance: 'PoseEngine | None' = None
    _lock = threading.Lock()

    def __init__(self, config=Config):
        from ultralytics import YOLO

        self.config = config
        model_path = os.path.join(config.MODEL_FOLDER, config.POSE_MODEL)
        logger.info('Loading pose model: %s', config.POSE_MODEL)
        self.model = YOLO(model_path)
        self._infer_lock = threading.Lock()
        self._last_warning_ts = 0.0

    @classmethod
    def get(cls) -> 'PoseEngine | None':
        if not Config.POSE_ENABLED:
            return None
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    try:
                        cls._instance = PoseEngine()
                    except Exception as e:
                        logger.warning('PoseEngine init failed: %s', e)
                        cls._instance = None
        return cls._instance

    def analyze(self, frame, density: float = 0.0) -> PoseFeatures:
        feats = PoseFeatures()
        try:
            with self._infer_lock:
                results = self.model.predict(
                    frame,
                    conf=0.25,
                    iou=0.5,
                    verbose=False,
                )
        except Exception as e:
            now = time.time()
            if now - self._last_warning_ts > 60:
                logger.warning('Pose inference failed: %s', e)
                self._last_warning_ts = now
            return feats

        if not results:
            return feats
        r = results[0]
        kps = getattr(r, 'keypoints', None)
        if kps is None or kps.xy is None:
            return feats

        xy = kps.xy.cpu().numpy()        # (N, 17, 2)
        conf = kps.conf.cpu().numpy() if kps.conf is not None else np.ones(xy.shape[:2])

        feats.n_persons = int(xy.shape[0])

        for i in range(xy.shape[0]):
            p_xy = xy[i]
            p_conf = conf[i]

            tags: list[str] = []
            if _is_fallen(p_xy, p_conf):
                feats.n_fallen += 1
                tags.append('FALLEN')
            if _is_compressed(p_xy, p_conf):
                feats.n_compressed += 1
                tags.append('COMPRESSED')
            if _is_arms_up(p_xy, p_conf):
                feats.n_arms_up += 1
                tags.append('ARMS_UP')

            if tags:
                feats.per_person.append({'idx': i, 'tags': tags})

        feats.crush_risk = _blend_crush_risk(feats, density)
        return feats


def _kp_ok(conf_row, idx) -> bool:
    return conf_row[idx] >= _KP_CONF_MIN


def _is_fallen(xy, conf) -> bool:
    if not (_kp_ok(conf, _KP['l_shoulder']) and _kp_ok(conf, _KP['l_hip'])):
        return False
    sx, sy = xy[_KP['l_shoulder']]
    hx, hy = xy[_KP['l_hip']]
    dx, dy = hx - sx, hy - sy
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1:
        return False
    # Angle from vertical; ~0° = upright, ~90° = horizontal
    angle_deg = abs(np.degrees(np.arctan2(abs(dx), abs(dy) + 1e-6)))
    return angle_deg > 60.0


def _is_compressed(xy, conf) -> bool:
    sh_ok = _kp_ok(conf, _KP['l_shoulder']) and _kp_ok(conf, _KP['r_shoulder'])
    hp_ok = _kp_ok(conf, _KP['l_hip']) and _kp_ok(conf, _KP['r_hip'])
    if not (sh_ok and hp_ok):
        return False
    sy = (xy[_KP['l_shoulder']][1] + xy[_KP['r_shoulder']][1]) / 2.0
    hy = (xy[_KP['l_hip']][1] + xy[_KP['r_hip']][1]) / 2.0
    sw = abs(xy[_KP['l_shoulder']][0] - xy[_KP['r_shoulder']][0])
    torso_len = abs(hy - sy)
    if sw < 1:
        return False
    # Typical upright torso is 1.5–2.2× shoulder width.
    # Heavy compression when torso<0.6× shoulder width.
    return torso_len < 0.6 * sw


def _is_arms_up(xy, conf) -> bool:
    need = [_KP['l_shoulder'], _KP['r_shoulder'], _KP['l_wrist'], _KP['r_wrist']]
    if not all(_kp_ok(conf, k) for k in need):
        return False
    l_wrist_up = xy[_KP['l_wrist']][1] < xy[_KP['l_shoulder']][1]
    r_wrist_up = xy[_KP['r_wrist']][1] < xy[_KP['r_shoulder']][1]
    return bool(l_wrist_up and r_wrist_up)


def _blend_crush_risk(feats: PoseFeatures, density: float) -> float:
    if feats.n_persons == 0:
        return 0.0
    fall_ratio = feats.n_fallen / feats.n_persons
    comp_ratio = feats.n_compressed / feats.n_persons
    panic_ratio = feats.n_arms_up / feats.n_persons

    # Weight heavily on fallen + compressed; arms-up is an amplifier.
    base = 0.6 * fall_ratio + 0.3 * comp_ratio + 0.1 * panic_ratio

    # Density multiplier: density >= 6 p/m² is ISO crush zone.
    density_mult = min(1.5, 1.0 + density / 10.0)
    return float(min(1.0, base * density_mult))


def analyze_frame(frame, density: float = 0.0) -> PoseFeatures | None:
    """Convenience: get the shared engine and analyze."""
    engine = PoseEngine.get()
    if engine is None:
        return None
    return engine.analyze(frame, density=density)
