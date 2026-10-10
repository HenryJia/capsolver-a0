"""Configuration handling for the Capsolver plugin.

The plugin reads settings from the Agent Zero plugin config (Settings > Agent >
Capsolver) and falls back to the standard ``CAPSOLVER_API_KEY`` environment
variable so the plugin also works in headless / server deployments.
"""

from __future__ import annotations

import os
from typing import Any

from helpers import plugins

PLUGIN_NAME = "capsolver"
DEFAULT_SERVICE = "https://api.capsolver.com"
DEFAULT_REQUEST_TIMEOUT = 30.0
DEFAULT_TIMEOUT = 120.0
DEFAULT_POLLING_INTERVAL = 5.0
DEFAULT_AUTOFILL = True


def load_config(agent: Any | None = None) -> dict[str, Any]:
    """Return the effective plugin configuration as a dict (never ``None``)."""
    try:
        config = plugins.get_plugin_config(PLUGIN_NAME, agent=agent) or {}
    except Exception:
        config = {}
    if not isinstance(config, dict):
        return {}
    return config


def _to_float(value: Any, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        result = float(value)
        return result if result > 0 else default
    except (TypeError, ValueError):
        return default


def resolve_api_key(config: dict[str, Any]) -> str:
    """Resolve the API key from config first, then the environment."""
    key = str(config.get("api_key") or "").strip()
    if key:
        return key
    return str(os.environ.get("CAPSOLVER_API_KEY", "")).strip()


def build_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw config into typed solver settings."""
    autofill = config.get("autofill", DEFAULT_AUTOFILL)
    if isinstance(autofill, str):
        autofill = autofill.strip().lower() not in {"", "0", "false", "no", "off"}
    return {
        "api_key": resolve_api_key(config),
        "service": str(config.get("service") or DEFAULT_SERVICE).strip() or DEFAULT_SERVICE,
        "request_timeout": _to_float(config.get("request_timeout"), DEFAULT_REQUEST_TIMEOUT),
        "default_timeout": _to_float(config.get("default_timeout"), DEFAULT_TIMEOUT),
        "polling_interval": _to_float(config.get("polling_interval"), DEFAULT_POLLING_INTERVAL),
        "autofill": bool(autofill),
    }
