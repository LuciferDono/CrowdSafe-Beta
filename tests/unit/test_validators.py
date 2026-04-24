"""Validator unit tests."""
from __future__ import annotations

from backend.utils import validators as v


class TestEmail:
    def test_valid(self):
        assert v.validate_email('user@example.com')
        assert v.validate_email('a.b+tag@sub.domain.co')

    def test_invalid(self):
        assert not v.validate_email('not-an-email')
        assert not v.validate_email('missing@tld')
        assert not v.validate_email('@no-local.part')


class TestUsername:
    def test_valid(self):
        assert v.validate_username('user_1')
        assert v.validate_username('operator')

    def test_too_short(self):
        assert not v.validate_username('ab')

    def test_bad_chars(self):
        assert not v.validate_username('user-with-dash')
        assert not v.validate_username('user with space')

    def test_too_long(self):
        assert not v.validate_username('x' * 51)


class TestPassword:
    def test_min_length(self):
        assert v.validate_password('abcdef')
        assert not v.validate_password('short')


class TestVideoFile:
    def test_allowed_ext(self):
        assert v.allowed_video_file('clip.mp4')
        assert v.allowed_video_file('CLIP.MP4')
        assert v.allowed_video_file('movie.webm')

    def test_disallowed(self):
        assert not v.allowed_video_file('photo.jpg')
        assert not v.allowed_video_file('no_extension')
        assert not v.allowed_video_file('.env')


class TestSourceType:
    def test_allowed(self):
        for s in ('rtsp', 'http', 'file', 'usb'):
            assert v.validate_source_type(s)

    def test_disallowed(self):
        assert not v.validate_source_type('ftp')
        assert not v.validate_source_type('')


class TestSanitize:
    def test_trims_whitespace(self):
        assert v.sanitize_string('  hello  ') == 'hello'

    def test_truncates(self):
        assert len(v.sanitize_string('x' * 1000, max_length=10)) == 10

    def test_non_string_returns_empty(self):
        assert v.sanitize_string(12345) == ''
        assert v.sanitize_string(None) == ''
