"""Tests for tetodl.utils.hooks."""

import sys
from io import StringIO

import pytest

from tetodl.utils.hooks import (
    get_progress_hook,
    QuietLogger,
    get_postprocessor_hook,
    EncodingSpinnerHook,
)


class TestGetProgressHook:
    def test_minimal_style_returns_callable(self):
        hook = get_progress_hook("minimal")
        assert callable(hook)

    def test_classic_style_returns_callable(self):
        hook = get_progress_hook("classic")
        assert callable(hook)


class TestGetPostprocessorHook:
    def test_returns_encoding_spinner_hook(self):
        hook = get_postprocessor_hook("Processing...")
        assert isinstance(hook, EncodingSpinnerHook)
        assert hook.text == "Processing..."
        assert hook.is_running is False


class TestQuietLogger:
    @pytest.fixture
    def logger(self):
        return QuietLogger()

    def test_debug_suppresses(self, logger):
        out = StringIO()
        old = sys.stdout
        sys.stdout = out
        try:
            logger.debug("should not appear")
            assert out.getvalue() == ""
        finally:
            sys.stdout = old

    def test_warning_suppresses(self, logger):
        out = StringIO()
        old = sys.stdout
        sys.stdout = out
        try:
            logger.warning("should not appear")
            assert out.getvalue() == ""
        finally:
            sys.stdout = old

    def test_error_output(self, logger):
        out = StringIO()
        old = sys.stdout
        sys.stdout = out
        try:
            logger.error("something went wrong")
            written = out.getvalue()
            assert "something went wrong" in written
        finally:
            sys.stdout = old

    def test_error_403_suppressed(self, logger):
        out = StringIO()
        old = sys.stdout
        sys.stdout = out
        try:
            logger.error("403 Forbidden")
            assert "403" not in out.getvalue()
        finally:
            sys.stdout = old


class TestEncodingSpinnerHook:
    @pytest.fixture
    def hook(self):
        return EncodingSpinnerHook("Encoding...")

    def test_started_status_sets_is_running(self, hook, mocker):
        mocker.patch("tetodl.utils.hooks.console.proc")
        hook({"status": "started"})
        assert hook.is_running is True

    def test_finished_status_clears(self, hook, mocker):
        mocker.patch("tetodl.utils.hooks.console.proc")
        hook({"status": "started"})
        hook({"status": "finished"})
        assert hook.is_running is False
