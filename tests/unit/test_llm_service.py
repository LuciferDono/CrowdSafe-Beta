"""LLM service unit tests.

Network calls are mocked — we're validating the wiring, retry semantics, and
helper logic, not the OpenRouter API itself.
"""
from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import pytest

from backend.services import llm_service as ls


class TestResolveModel:
    def test_explicit_model_wins(self):
        assert ls._resolve_model('premium', 'some/other-model') == 'some/other-model'

    def test_default_tier(self):
        from config import Config
        assert ls._resolve_model(None, None) == Config.OR_MODEL_DEFAULT

    def test_premium_tier(self):
        from config import Config
        assert ls._resolve_model('premium', None) == Config.OR_MODEL_PREMIUM

    def test_vision_tier(self):
        from config import Config
        assert ls._resolve_model('vision', None) == Config.OR_MODEL_VISION

    def test_unknown_tier_falls_back_to_default(self):
        from config import Config
        assert ls._resolve_model('bogus-tier', None) == Config.OR_MODEL_DEFAULT


class TestEncodeImage:
    def test_passthrough_http_url(self):
        assert ls._encode_image('https://example.com/img.png') == 'https://example.com/img.png'

    def test_passthrough_data_url(self):
        url = 'data:image/jpeg;base64,AAAA'
        assert ls._encode_image(url) == url

    def test_bytes_become_data_url(self):
        payload = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # JPEG magic
        result = ls._encode_image(payload)
        assert result.startswith('data:image/jpeg;base64,')
        assert base64.b64decode(result.split(',', 1)[1]) == payload

    def test_bad_input_raises(self):
        with pytest.raises(ls.LLMError):
            ls._encode_image(12345)  # type: ignore[arg-type]

    def test_missing_path_raises(self):
        with pytest.raises(ls.LLMError):
            ls._encode_image('/nonexistent/path/to.jpg')


class TestHeaders:
    def test_raises_without_api_key(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'OR_API_KEY', '')
        with pytest.raises(ls.LLMError):
            ls._headers()

    def test_includes_referer_and_title(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'OR_API_KEY', 'sk-test')
        h = ls._headers()
        assert h['Authorization'] == 'Bearer sk-test'
        assert 'HTTP-Referer' in h
        assert 'X-Title' in h


class TestChat:
    def test_happy_path(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'OR_API_KEY', 'sk-test')
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {
            'model': 'test-model',
            'choices': [{'message': {'content': 'hello world'}}],
            'usage': {'total_tokens': 5},
        }

        with patch('backend.services.llm_service.requests.post', return_value=mock_resp) as post:
            out = ls.chat([{'role': 'user', 'content': 'hi'}])
            assert out.text == 'hello world'
            assert out.usage == {'total_tokens': 5}
            post.assert_called_once()

    def test_retries_on_5xx(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'OR_API_KEY', 'sk-test')
        fail = MagicMock(status_code=502, ok=False, text='bad gateway')
        fail.json.side_effect = ValueError
        ok = MagicMock(status_code=200, ok=True)
        ok.json.return_value = {
            'model': 'm',
            'choices': [{'message': {'content': 'ok'}}],
            'usage': {},
        }

        with patch('backend.services.llm_service.requests.post', side_effect=[fail, ok]), \
             patch('backend.services.llm_service.time.sleep'):
            out = ls.chat([{'role': 'user', 'content': 'hi'}], max_retries=2)
            assert out.text == 'ok'

    def test_hard_fail_on_400(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'OR_API_KEY', 'sk-test')
        bad = MagicMock(status_code=400, ok=False, text='bad request')

        with patch('backend.services.llm_service.requests.post', return_value=bad):
            with pytest.raises(ls.LLMError):
                ls.chat([{'role': 'user', 'content': 'hi'}], max_retries=0)


class TestLLMResponseJson:
    def test_plain_json(self):
        r = ls.LLMResponse(text='{"a": 1}', model='m', usage={}, raw={})
        assert r.json() == {'a': 1}

    def test_markdown_fenced_json(self):
        r = ls.LLMResponse(text='```json\n{"a": 1}\n```', model='m', usage={}, raw={})
        assert r.json() == {'a': 1}


class TestIsConfigured:
    def test_true_when_key_set(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'OR_API_KEY', 'sk-test')
        assert ls.is_configured() is True

    def test_false_when_unset(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'OR_API_KEY', '')
        assert ls.is_configured() is False
