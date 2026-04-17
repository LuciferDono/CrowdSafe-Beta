"""HuggingFace gateway.

Two concerns:
  1. Model downloads to the local ``models/`` folder via huggingface_hub
     (cached, resumable, SHA-verified).
  2. Inference API calls for hosted models (zero-install remote inference).

Keeps HF_TOKEN in one place; downstream services (pose, depth, ReID, etc.)
ask this module for a local path or a hosted prediction.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

from config import Config

logger = logging.getLogger(__name__)

_INFERENCE_BASE = 'https://api-inference.huggingface.co/models'


class HFError(Exception):
    """Raised when an HF operation fails."""


def is_configured() -> bool:
    return bool(Config.HF_TOKEN)


def _headers(extra: dict | None = None) -> dict:
    if not Config.HF_TOKEN:
        raise HFError('HF_TOKEN not configured')
    h = {'Authorization': f'Bearer {Config.HF_TOKEN}'}
    if extra:
        h.update(extra)
    return h


def download_model(
    repo_id: str,
    filename: str | None = None,
    *,
    revision: str | None = None,
    local_dir: str | None = None,
) -> str:
    """Download a single file (or snapshot) and return the local path.

    - If ``filename`` is given: fetches that one weight file (fast path for
      YOLO-style single-artifact repos).
    - Otherwise: snapshot_download of the whole repo.
    """
    try:
        from huggingface_hub import hf_hub_download, snapshot_download
    except ImportError as e:
        raise HFError(f'huggingface_hub not installed: {e}') from e

    target = local_dir or os.path.join(Config.MODEL_FOLDER, repo_id.replace('/', '__'))
    os.makedirs(target, exist_ok=True)

    try:
        if filename:
            return hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                revision=revision,
                token=Config.HF_TOKEN or None,
                local_dir=target,
            )
        return snapshot_download(
            repo_id=repo_id,
            revision=revision,
            token=Config.HF_TOKEN or None,
            local_dir=target,
        )
    except Exception as e:
        raise HFError(f'download failed for {repo_id}: {e}') from e


def infer(
    model: str,
    payload: Any,
    *,
    task: str | None = None,
    timeout: float = 30.0,
    max_retries: int = 2,
    wait_for_model: bool = True,
) -> Any:
    """Call the hosted HF Inference API.

    ``payload`` is forwarded as JSON if dict/list, else as raw bytes.
    ``task`` is informational only (HF routes by model name).
    """
    url = f'{_INFERENCE_BASE}/{model}'
    headers = _headers()
    options = {'wait_for_model': wait_for_model}

    if isinstance(payload, (bytes, bytearray)):
        body = bytes(payload)
        json_body = None
        headers['Content-Type'] = 'application/octet-stream'
    else:
        body = None
        json_body = {'inputs': payload, 'options': options}

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            r = requests.post(
                url,
                headers=headers,
                data=body,
                json=json_body,
                timeout=timeout,
            )
            if r.status_code == 503:
                raise HFError(f'model loading (503): {r.text[:200]}')
            if r.status_code == 429 or 500 <= r.status_code < 600:
                raise HFError(f'transient {r.status_code}: {r.text[:200]}')
            if not r.ok:
                raise HFError(f'{r.status_code}: {r.text[:500]}')
            ctype = r.headers.get('Content-Type', '')
            if ctype.startswith('application/json'):
                return r.json()
            return r.content
        except Exception as e:
            last_err = e
            if attempt >= max_retries:
                break
            sleep = 1.0 * (2 ** attempt)
            logger.warning(
                'HF inference failed (attempt %d, model=%s): %s — retry in %.1fs',
                attempt + 1, model, e, sleep,
            )
            time.sleep(sleep)
    raise HFError(f'HF inference failed for {model}: {last_err}')
