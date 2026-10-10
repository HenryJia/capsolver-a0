"""Factory helpers for building configured capsolver-core clients."""

from __future__ import annotations

from typing import Any

from capsolver_core import Capsolver


class MissingApiKeyError(RuntimeError):
    """Raised when no Capsolver API key is configured."""


_MISSING_KEY_MESSAGE = (
    "Capsolver API key is not configured. Add it in Settings > Agent > "
    "Capsolver, or set the CAPSOLVER_API_KEY environment variable."
)


def require_api_key(settings: dict[str, Any]) -> str:
    """Return the configured API key or raise a clear, actionable error."""
    key = str(settings.get("api_key") or "").strip()
    if not key:
        raise MissingApiKeyError(_MISSING_KEY_MESSAGE)
    return key


def build_client(settings: dict[str, Any]) -> Capsolver:
    """Create a capsolver-core client from normalized plugin settings."""
    api_key = require_api_key(settings)
    return Capsolver(
        api_key=api_key,
        service=str(settings.get("service") or "https://api.capsolver.com"),
        default_timeout=float(settings.get("default_timeout") or 120.0),
        polling_interval=float(settings.get("polling_interval") or 5.0),
        request_timeout_ms=int(float(settings.get("request_timeout") or 30.0) * 1000),
    )
