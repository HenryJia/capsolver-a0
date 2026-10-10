"""Unit tests for the Capsolver plugin.

These cover the pure logic that does not need network access or a live
browser: configuration normalization, the Agent Zero page-driver adapter, and
browser-id resolution.
"""

from __future__ import annotations

import json

import pytest

from usr.plugins.capsolver.helpers import config as config_helper
from usr.plugins.capsolver.helpers.page_driver import A0PageDriver, _extract_result, _inline_arg
from usr.plugins.capsolver.helpers import solver


class FakeRuntime:
    """Minimal stand-in for Agent Zero's browser runtime session."""

    def __init__(self, *, evaluate_result=None, state=None, listing=None):
        self._evaluate_result = evaluate_result
        self._state = state or {"currentUrl": "https://example.com"}
        self._listing = listing or {"browsers": [{"id": 1}], "last_interacted_browser_id": 1}
        self.calls = []

    async def call(self, method, *args, **kwargs):
        self.calls.append((method, args, kwargs))
        if method == "evaluate":
            return {"result": self._evaluate_result}
        if method == "state":
            return self._state
        if method == "list":
            return self._listing
        raise AssertionError(f"unexpected method {method}")


# ── config ────────────────────────────────────────────────────────


def test_build_settings_defaults():
    settings = config_helper.build_settings({})
    assert settings["service"] == config_helper.DEFAULT_SERVICE
    assert settings["default_timeout"] == config_helper.DEFAULT_TIMEOUT
    assert settings["polling_interval"] == config_helper.DEFAULT_POLLING_INTERVAL
    assert settings["autofill"] is True
    assert settings["api_key"] == ""


def test_build_settings_env_fallback(monkeypatch):
    monkeypatch.setenv("CAPSOLVER_API_KEY", "ENV-KEY")
    settings = config_helper.build_settings({})
    assert settings["api_key"] == "ENV-KEY"


def test_config_key_wins_over_env(monkeypatch):
    monkeypatch.setenv("CAPSOLVER_API_KEY", "ENV-KEY")
    settings = config_helper.build_settings({"api_key": "CFG-KEY"})
    assert settings["api_key"] == "CFG-KEY"


def test_build_settings_autofill_string_coercion():
    assert config_helper.build_settings({"autofill": "false"})["autofill"] is False
    assert config_helper.build_settings({"autofill": "yes"})["autofill"] is True
    assert config_helper.build_settings({"autofill": ""})["autofill"] is False


def test_build_settings_invalid_numbers_use_defaults():
    settings = config_helper.build_settings(
        {"default_timeout": "abc", "polling_interval": -3, "request_timeout": None}
    )
    assert settings["default_timeout"] == config_helper.DEFAULT_TIMEOUT
    assert settings["polling_interval"] == config_helper.DEFAULT_POLLING_INTERVAL
    assert settings["request_timeout"] == config_helper.DEFAULT_REQUEST_TIMEOUT


# ── page driver ───────────────────────────────────────────────────


def test_inline_arg_serializes_values():
    assert _inline_arg(None) == "undefined"
    assert _inline_arg({"a": 1}) == json.dumps({"a": 1})
    assert _inline_arg("x") == '"x"'


def test_extract_result_unwraps_dict():
    assert _extract_result({"result": 5}) == 5
    assert _extract_result({"result": None}) is None
    assert _extract_result(7) == 7


@pytest.mark.asyncio
async def test_driver_evaluate_builds_iife():
    runtime = FakeRuntime(evaluate_result=[1, 2])
    driver = A0PageDriver(runtime, 3)
    result = await driver.evaluate("() => [1,2]")
    assert result == [1, 2]
    method, args, _ = runtime.calls[0]
    assert method == "evaluate"
    assert args[0] == 3
    assert args[1] == "(() => [1,2])(undefined)"


@pytest.mark.asyncio
async def test_driver_evaluate_passes_argument():
    runtime = FakeRuntime(evaluate_result=True)
    driver = A0PageDriver(runtime, 1)
    await driver.evaluate("(a) => a", {"token": "t"})
    assert runtime.calls[0][1][1] == '((a) => a)({"token": "t"})'


@pytest.mark.asyncio
async def test_driver_url_reads_state():
    runtime = FakeRuntime(state={"currentUrl": "https://page.test/x"})
    driver = A0PageDriver(runtime, 1)
    assert await driver.url() == "https://page.test/x"


# ── solver browser resolution ─────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_browser_id_explicit():
    runtime = FakeRuntime()
    assert await solver._resolve_browser_id(runtime, 9) == 9
    assert runtime.calls == []


@pytest.mark.asyncio
async def test_resolve_browser_id_uses_last_interacted():
    runtime = FakeRuntime(
        listing={"browsers": [{"id": 1}, {"id": 2}], "last_interacted_browser_id": 2}
    )
    assert await solver._resolve_browser_id(runtime, None) == 2


@pytest.mark.asyncio
async def test_resolve_browser_id_no_tabs_raises():
    runtime = FakeRuntime(listing={"browsers": [], "last_interacted_browser_id": None})
    with pytest.raises(RuntimeError):
        await solver._resolve_browser_id(runtime, None)


# ── supported types ───────────────────────────────────────────────


def test_supported_captchas_lists_expected():
    result = solver.get_supported_captchas()
    assert result["success"] is True
    assert result["captcha_types"] == ["cloudflare", "reCaptchaV2", "reCaptchaV3"]
