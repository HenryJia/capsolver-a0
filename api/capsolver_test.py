"""API handler backing the Settings 'Test Connection' button.

Validates the supplied (or saved) Capsolver API key by fetching the account
balance. Returns the balance on success and a clean error otherwise.
"""

from __future__ import annotations

from helpers.api import ApiHandler, Request, Response

from usr.plugins.capsolver.helpers import config as config_helper
from usr.plugins.capsolver.helpers.client import build_client


class CapsolverTest(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        submitted_key = str(input.get("api_key") or "").strip()

        settings = config_helper.build_settings(config_helper.load_config())
        if submitted_key:
            settings["api_key"] = submitted_key

        if not settings.get("api_key"):
            return {
                "success": False,
                "error": "No API key provided. Enter a key or set CAPSOLVER_API_KEY.",
            }

        client = build_client(settings)
        try:
            balance = await client.get_balance()
        except Exception as exc:  # noqa: BLE001 - report failure to the UI
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

        return {
            "success": True,
            "balance": balance.balance,
            "packages": balance.packages,
        }
