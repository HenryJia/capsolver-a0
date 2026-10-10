"""Adapter exposing an Agent Zero browser tab as a capsolver-core PageDriver.

capsolver-core works against a minimal page interface (evaluate, url,
wait_for_selector). Agent Zero's browser runtime exposes a different surface:
runtime.call("evaluate", browser_id, script) and runtime.call("state",
browser_id). This module bridges the two so Capsolver can read and modify the
page inside the Agent Zero browser session the agent is already using, instead
of launching a second browser.
"""

from __future__ import annotations

import json
from typing import Any


class A0PageDriver:
    """A capsolver-core compatible driver backed by an Agent Zero browser tab."""

    def __init__(self, runtime: Any, browser_id: int | str) -> None:
        self._runtime = runtime
        self._browser_id = browser_id

    async def evaluate(self, script: str, arg: Any = None) -> Any:
        """Run a JavaScript function on the page and return its result.

        Agent Zero's evaluate takes only a script string, so the argument is
        inlined by turning the snippet into an immediately-invoked expression.
        Agent Zero evaluates this in the page's main world, which is required
        to read the captcha widgets' own globals (for example
        ___grecaptcha_cfg).
        """
        expression = f"({script})({_inline_arg(arg)})"
        payload = await self._runtime.call("evaluate", self._browser_id, expression)
        return _extract_result(payload)

    async def url(self) -> str:
        """Return the tab's current URL."""
        state = await self._runtime.call("state", self._browser_id)
        if isinstance(state, dict):
            return str(state.get("currentUrl") or state.get("url") or "")
        return ""

    async def wait_for_selector(self, selector: str, *, timeout: float | None = None) -> None:
        """Best-effort selector wait.

        Detection and solving do not require it, and Agent Zero's runtime does
        not expose a portable wait primitive, so this is intentionally a no-op
        that keeps the driver interface complete without overreaching.
        """
        return None


def _inline_arg(arg: Any) -> str:
    if arg is None:
        return "undefined"
    return json.dumps(arg)


def _extract_result(payload: Any) -> Any:
    """Unwrap the result field from Agent Zero's evaluate response."""
    if isinstance(payload, dict):
        if "result" in payload:
            return payload["result"]
        if payload.get("ok") and "result" in payload:
            return payload["result"]
    return payload
