"""Agent-facing Capsolver tool.

Lets the agent detect and solve captchas on pages opened in Agent Zero's own
browser, plus check account balance and supported captcha types.
"""

from __future__ import annotations

import json
from typing import Any

from helpers.tool import Response, Tool

from usr.plugins.capsolver.helpers import solver
from usr.plugins.capsolver.helpers.client import MissingApiKeyError


class Capsolver(Tool):
    """Solve captchas (reCAPTCHA v2/v3, Cloudflare Turnstile) via Capsolver."""

    async def execute(self, action: str = "", **kwargs: Any) -> Response:
        method = str(self.method or "").strip().lower().replace("-", "_")
        requested = str(action or "").strip().lower().replace("-", "_")
        resolved_action = requested or method or "detect"

        try:
            payload = await self._dispatch(resolved_action, kwargs)
        except MissingApiKeyError as exc:
            return self._respond(
                {"success": False, "error": str(exc), "error_type": "missing_api_key"}
            )
        except ValueError as exc:
            return self._respond(
                {"success": False, "error": str(exc), "error_type": "invalid_argument"}
            )
        except Exception as exc:  # noqa: BLE001 - surface a clean tool error
            return self._respond(
                {"success": False, "error": str(exc), "error_type": type(exc).__name__}
            )

        return self._respond(payload)

    async def _dispatch(self, action: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        if action in {"detect", "detect_captchas"}:
            return await solver.detect_captchas(
                self.agent, browser_id=kwargs.get("browser_id")
            )

        if action in {"solve", "solve_captcha"}:
            return await solver.solve_token(
                self.agent,
                captcha_type=str(kwargs.get("captcha_type") or ""),
                website_url=str(kwargs.get("website_url") or ""),
                website_key=str(kwargs.get("website_key") or ""),
                version=kwargs.get("version"),
                page_action=kwargs.get("page_action"),
                min_score=_opt_float(kwargs.get("min_score")),
                invisible=_opt_bool(kwargs.get("invisible")),
                enterprise=_opt_bool(kwargs.get("enterprise")),
                s_token=kwargs.get("s_token"),
                cdata=kwargs.get("cdata"),
                proxy=kwargs.get("proxy"),
                user_agent=kwargs.get("user_agent"),
                timeout=_opt_float(kwargs.get("timeout")),
                polling_interval=_opt_float(kwargs.get("polling_interval")),
            )

        if action in {"solve_on_page", "solve_page", "auto"}:
            return await solver.solve_on_page(
                self.agent,
                browser_id=kwargs.get("browser_id"),
                autofill=_opt_bool(kwargs.get("autofill")),
                timeout=_opt_float(kwargs.get("timeout")),
                polling_interval=_opt_float(kwargs.get("polling_interval")),
            )

        if action in {"balance", "get_balance"}:
            return await solver.get_balance(self.agent)

        if action in {"supported", "get_supported_captchas", "types"}:
            return solver.get_supported_captchas()

        raise ValueError(
            f"Unknown action '{action}'. Use one of: detect, solve, solve_on_page, "
            "balance, supported."
        )

    def _respond(self, payload: dict[str, Any]) -> Response:
        return Response(message=json.dumps(payload, ensure_ascii=False), break_loop=False)


def _opt_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _opt_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
