"""VLM-powered natural-language alert narration.

Takes a JPEG frame + metrics dict and produces a single, human-readable
sentence describing what's happening. Falls back silently when
OR_API_KEY is missing so the alert pipeline never blocks on LLM.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.services import llm_service

logger = logging.getLogger('alert_narrator')

_SYSTEM = (
    "You narrate crowd-safety alerts for a live operator console. "
    "Write ONE sentence (<=30 words), plain English, no emoji, no hedging. "
    "State: rough crowd size, whether density is heavy/moderate, whether motion "
    "is stagnant/flowing, and the most likely immediate risk. Do NOT invent "
    "specific numbers the operator can already see."
)


def narrate(
    metrics: dict,
    frame_jpeg: bytes | None = None,
    *,
    camera_name: str | None = None,
) -> str | None:
    """Return a one-sentence narrative, or None if unavailable."""
    if not llm_service.is_configured():
        return None

    cam_ctx = f"Camera: {camera_name}. " if camera_name else ""
    metrics_ctx = _summarize_metrics(metrics)
    prompt = (
        f"{cam_ctx}{metrics_ctx}\n"
        "Describe the scene and the risk in one sentence for an operator."
    )

    try:
        if frame_jpeg:
            return llm_service.vision(
                prompt,
                images=[frame_jpeg],
                system=_SYSTEM,
                tier='vision',
                max_tokens=120,
                temperature=0.2,
            ).strip()
        return llm_service.simple(
            prompt,
            system=_SYSTEM,
            tier='default',
            max_tokens=120,
            temperature=0.2,
        ).strip()
    except Exception as e:
        logger.warning('VLM narration failed: %s', e)
        return None


def _summarize_metrics(metrics: dict[str, Any]) -> str:
    def _g(k, default=None):
        v = metrics.get(k, default)
        return v if v is not None else default

    parts = [
        f"risk={_g('risk_level', 'UNKNOWN')}",
        f"count={_g('count', 0)}",
        f"density={_g('density', 0):.2f} p/m^2" if isinstance(_g('density'), (int, float)) else "density=?",
        f"avg_velocity={_g('avg_velocity', 0):.2f} m/s" if isinstance(_g('avg_velocity'), (int, float)) else "avg_velocity=?",
        f"surge_rate={_g('surge_rate', 0):.2f}" if isinstance(_g('surge_rate'), (int, float)) else "surge_rate=?",
    ]
    return "Metrics: " + ", ".join(parts) + "."
