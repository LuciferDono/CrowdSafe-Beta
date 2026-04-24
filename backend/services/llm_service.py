"""OpenRouter LLM gateway.

Thin client around the OpenAI-compatible OpenRouter Chat Completions API.
Supports text, vision (image_url), structured JSON responses, and tiered
model selection via Config.OR_MODEL_{DEFAULT,PREMIUM,VISION,NANO}.
"""
from __future__ import annotations

import base64
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Iterable

import requests

from config import Config

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM call fails unrecoverably."""


@dataclass
class LLMResponse:
    text: str
    model: str
    usage: dict
    raw: dict

    def json(self) -> Any:
        import json

        payload = (self.text or '').strip()
        if not payload:
            finish = ''
            try:
                finish = self.raw['choices'][0].get('finish_reason', '') or ''
            except Exception:
                pass
            hint = ' (model returned empty content; check finish_reason={!r} — reasoning models may consume max_tokens budget)'.format(finish)
            raise LLMError('empty model response' + hint)
        if payload.startswith('```'):
            payload = payload.strip('`').lstrip('json').strip()
        return json.loads(payload)


_TIER_MAP = {
    'default': 'OR_MODEL_DEFAULT',
    'premium': 'OR_MODEL_PREMIUM',
    'vision': 'OR_MODEL_VISION',
    'nano': 'OR_MODEL_NANO',
}


def _resolve_model(tier: str | None, model: str | None) -> str:
    if model:
        return model
    attr = _TIER_MAP.get((tier or 'default').lower(), 'OR_MODEL_DEFAULT')
    return getattr(Config, attr)


def _headers() -> dict:
    if not Config.OR_API_KEY:
        raise LLMError('OR_API_KEY not configured')
    return {
        'Authorization': f'Bearer {Config.OR_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': Config.OR_SITE_URL,
        'X-Title': Config.OR_APP_NAME,
    }


def _encode_image(image: str | bytes) -> str:
    """Return data URL for image bytes/path/existing URL."""
    if isinstance(image, str):
        if image.startswith(('http://', 'https://', 'data:')):
            return image
        if os.path.exists(image):
            with open(image, 'rb') as f:
                data = f.read()
            ext = os.path.splitext(image)[1].lstrip('.').lower() or 'jpeg'
            return f'data:image/{ext};base64,{base64.b64encode(data).decode()}'
        raise LLMError(f'image path not found: {image}')
    if isinstance(image, (bytes, bytearray)):
        return f'data:image/jpeg;base64,{base64.b64encode(bytes(image)).decode()}'
    raise LLMError('unsupported image payload type')


def chat(
    messages: list[dict],
    *,
    tier: str = 'default',
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 512,
    response_format: dict | None = None,
    timeout: float = 30.0,
    max_retries: int = 2,
) -> LLMResponse:
    """Low-level chat completion call."""
    url = f'{Config.OR_BASE_URL.rstrip("/")}/chat/completions'
    payload: dict[str, Any] = {
        'model': _resolve_model(tier, model),
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    if response_format is not None:
        payload['response_format'] = response_format

    headers = _headers()
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 429 or 500 <= r.status_code < 600:
                raise LLMError(f'transient {r.status_code}: {r.text[:200]}')
            if not r.ok:
                raise LLMError(f'{r.status_code}: {r.text[:500]}')
            data = r.json()
            choice = data['choices'][0]['message']
            return LLMResponse(
                text=choice.get('content') or '',
                model=data.get('model', payload['model']),
                usage=data.get('usage', {}),
                raw=data,
            )
        except Exception as e:
            last_err = e
            if attempt >= max_retries:
                break
            sleep = 0.5 * (2 ** attempt)
            logger.warning('LLM call failed (attempt %d): %s — retrying in %.1fs', attempt + 1, e, sleep)
            time.sleep(sleep)
    raise LLMError(f'LLM request failed: {last_err}')


def simple(
    prompt: str,
    *,
    system: str | None = None,
    tier: str = 'default',
    **kwargs,
) -> str:
    """One-shot text prompt → text response."""
    messages: list[dict] = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt})
    return chat(messages, tier=tier, **kwargs).text


def vision(
    prompt: str,
    images: Iterable[str | bytes],
    *,
    system: str | None = None,
    tier: str = 'vision',
    **kwargs,
) -> str:
    """Image(s) + prompt → text response."""
    content: list[dict] = [{'type': 'text', 'text': prompt}]
    for img in images:
        content.append({'type': 'image_url', 'image_url': {'url': _encode_image(img)}})

    messages: list[dict] = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': content})
    return chat(messages, tier=tier, **kwargs).text


def json_response(
    prompt: str,
    *,
    system: str | None = None,
    tier: str = 'nano',
    **kwargs,
) -> Any:
    """Prompt → parsed JSON object."""
    messages: list[dict] = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt})
    resp = chat(
        messages,
        tier=tier,
        response_format={'type': 'json_object'},
        **kwargs,
    )
    return resp.json()


def is_configured() -> bool:
    return bool(Config.OR_API_KEY)
