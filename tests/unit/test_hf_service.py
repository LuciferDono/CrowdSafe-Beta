"""HuggingFace gateway unit tests (network fully mocked)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.services import hf_service as hf


class TestIsConfigured:
    def test_true_when_token_set(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_test')
        assert hf.is_configured()

    def test_false_when_empty(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', '')
        assert not hf.is_configured()


class TestHeaders:
    def test_no_token_raises(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', '')
        with pytest.raises(hf.HFError):
            hf._headers()

    def test_with_extra(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_abc')
        h = hf._headers({'X-Test': '1'})
        assert h['Authorization'] == 'Bearer hf_abc'
        assert h['X-Test'] == '1'


class TestInfer:
    def _ok_response(self, content=b'{}', ctype='application/json', json_body=None):
        resp = MagicMock()
        resp.status_code = 200
        resp.ok = True
        resp.headers = {'Content-Type': ctype}
        resp.content = content
        resp.json = MagicMock(return_value=json_body or {'result': 'ok'})
        return resp

    def test_json_input_json_output(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_abc')

        with patch('backend.services.hf_service.requests.post',
                   return_value=self._ok_response(json_body={'label': 'ok'})) as post:
            out = hf.infer('org/model', {'inputs': 'text'})
            assert out == {'label': 'ok'}
            post.assert_called_once()

    def test_bytes_input_binary_output(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_abc')

        with patch('backend.services.hf_service.requests.post',
                   return_value=self._ok_response(content=b'binary', ctype='application/octet-stream')):
            out = hf.infer('org/model', b'audio-bytes')
            assert out == b'binary'

    def test_503_retries(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_abc')

        bad = MagicMock(status_code=503, ok=False, text='loading', headers={})
        ok = self._ok_response()

        with patch('backend.services.hf_service.requests.post', side_effect=[bad, ok]), \
             patch('backend.services.hf_service.time.sleep'):
            out = hf.infer('org/model', {'inputs': 'x'}, max_retries=2)
            assert out == {'result': 'ok'}

    def test_hard_fail_on_4xx(self, monkeypatch):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_abc')

        bad = MagicMock(status_code=401, ok=False, text='no', headers={})
        with patch('backend.services.hf_service.requests.post', return_value=bad), \
             patch('backend.services.hf_service.time.sleep'):
            with pytest.raises(hf.HFError):
                hf.infer('org/model', {'inputs': 'x'}, max_retries=0)


def _inject_hf_symbols(**fns):
    """Inject names into huggingface_hub.__dict__ to bypass lazy __getattr__.

    `from huggingface_hub import a, b` checks __dict__ for each name before
    falling back to __getattr__. Inject every name the SUT imports.
    """
    import huggingface_hub
    snapshot = {}
    for name, fn in fns.items():
        snapshot[name] = (name in huggingface_hub.__dict__,
                          huggingface_hub.__dict__.get(name))
        huggingface_hub.__dict__[name] = fn

    def _cleanup():
        for name, (had, prev) in snapshot.items():
            if had:
                huggingface_hub.__dict__[name] = prev
            else:
                huggingface_hub.__dict__.pop(name, None)

    return _cleanup


def _noop(**kw):
    return None


class TestDownloadModel:
    def test_single_file_path(self, monkeypatch, tmp_path):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_abc')
        monkeypatch.setattr(Config, 'MODEL_FOLDER', str(tmp_path))

        fake_path = str(tmp_path / 'file.bin')
        calls = []

        def _fake(**kw):
            calls.append(kw)
            return fake_path

        cleanup = _inject_hf_symbols(hf_hub_download=_fake, snapshot_download=_noop)
        try:
            out = hf.download_model('org/repo', filename='file.bin')
            assert out == fake_path
            assert len(calls) == 1
        finally:
            cleanup()

    def test_snapshot_path(self, monkeypatch, tmp_path):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_abc')
        monkeypatch.setattr(Config, 'MODEL_FOLDER', str(tmp_path))

        fake_dir = str(tmp_path / 'snapshot')
        calls = []

        def _fake(**kw):
            calls.append(kw)
            return fake_dir

        cleanup = _inject_hf_symbols(hf_hub_download=_noop, snapshot_download=_fake)
        try:
            out = hf.download_model('org/repo')
            assert out == fake_dir
            assert len(calls) == 1
        finally:
            cleanup()

    def test_wraps_exceptions(self, monkeypatch, tmp_path):
        from config import Config
        monkeypatch.setattr(Config, 'HF_TOKEN', 'hf_abc')
        monkeypatch.setattr(Config, 'MODEL_FOLDER', str(tmp_path))

        def _boom(**kw):
            raise RuntimeError('boom')

        cleanup = _inject_hf_symbols(hf_hub_download=_boom, snapshot_download=_noop)
        try:
            with pytest.raises(hf.HFError):
                hf.download_model('org/repo', filename='x')
        finally:
            cleanup()
