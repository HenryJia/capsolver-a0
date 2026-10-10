"""High-level captcha operations used by the agent-facing tool.

This module ties together three pieces:

* the Agent Zero browser runtime (which owns the live browser tab),
* the ``A0PageDriver`` adapter, and
* a configured ``capsolver-core`` client.

The public functions return plain JSON-serializable dicts so the tool layer
stays thin.
"""

from __future__ import annotations

from typing import Any

from capsolver_core import CaptchaInfo, CaptchaType, Solution
from capsolver_core.capsolver import SolveOnPageOptions
from capsolver_core.core.client import WaitOptions

from usr.plugins.capsolver.helpers import config as config_helper
from usr.plugins.capsolver.helpers.client import build_client
from usr.plugins.capsolver.helpers.page_driver import A0PageDriver

# Captcha families the Capsolver token API can solve directly.
TOKEN_CAPTCHA_TYPES = {
    CaptchaType.RECAPTCHA_V2.value,
    CaptchaType.RECAPTCHA_V3.value,
    CaptchaType.CLOUDFLARE.value,
}


async def _get_runtime(agent: Any) -> Any:
    """Return the browser runtime bound to the agent's chat."""
    from plugins._browser.helpers.selector import get_tool_runtime

    return await get_tool_runtime(agent)


async def _resolve_browser_id(runtime: Any, browser_id: int | str | None) -> int | str:
    """Resolve the target tab, defaulting to the last interacted one."""
    if browser_id is not None and str(browser_id).strip() != "":
        return browser_id
    listing = await runtime.call("list")
    browsers = listing.get("browsers") if isinstance(listing, dict) else None
    if not browsers:
        raise RuntimeError(
            "No browser tab is open. Open the target page with the browser tool first "
            "(action=open or action=navigate), then run the captcha action again."
        )
    last = listing.get("last_interacted_browser_id")
    if last is not None and any(b.get("id") == last for b in browsers):
        return last
    return browsers[0].get("id")


def _solution_to_dict(solution: Solution) -> dict[str, Any]:
    return {
        "captcha_type": solution.captcha_type.value,
        "token": solution.token,
        "expire_time": solution.expire_time,
        "user_agent": solution.user_agent,
    }


def _info_to_dict(info: CaptchaInfo) -> dict[str, Any]:
    return {
        "captcha_type": info.type.value,
        "website_url": info.website_url,
        "website_key": info.website_key,
        "version": info.version,
        "page_action": info.page_action,
        "invisible": info.invisible,
        "enterprise": info.enterprise,
        "cdata": info.cdata,
    }


async def detect_captchas(agent: Any, browser_id: int | str | None = None) -> dict[str, Any]:
    """Scan the active page for captchas. Does not require an API key."""
    runtime = await _get_runtime(agent)
    resolved = await _resolve_browser_id(runtime, browser_id)
    driver = A0PageDriver(runtime, resolved)
    settings = config_helper.build_settings(config_helper.load_config(agent))
    client = build_client({**settings, "api_key": settings.get("api_key") or "unused"})
    try:
        infos = await client.get_captcha_info(driver)
    finally:
        await client.aclose()
    return {
        "success": True,
        "browser_id": resolved,
        "url": await driver.url(),
        "detected_captchas": [info.type.value for info in infos],
        "captchas": [_info_to_dict(info) for info in infos],
    }


async def solve_token(
    agent: Any,
    captcha_type: str,
    website_url: str,
    website_key: str,
    *,
    version: str | None = None,
    page_action: str | None = None,
    min_score: float | None = None,
    invisible: bool | None = None,
    enterprise: bool | None = None,
    s_token: str | None = None,
    cdata: str | None = None,
    proxy: str | None = None,
    user_agent: str | None = None,
    timeout: float | None = None,
    polling_interval: float | None = None,
) -> dict[str, Any]:
    """Solve a captcha in token mode and return the token."""
    if captcha_type not in TOKEN_CAPTCHA_TYPES:
        raise ValueError(
            f"Unsupported captcha_type '{captcha_type}'. "
            f"Expected one of: {sorted(TOKEN_CAPTCHA_TYPES)}"
        )
    if not website_url:
        raise ValueError("website_url is required")
    if not website_key:
        raise ValueError("website_key is required")

    settings = config_helper.build_settings(config_helper.load_config(agent))
    client = build_client(settings)
    try:
        info = CaptchaInfo(
            type=CaptchaType(captcha_type),
            website_url=website_url,
            website_key=website_key,
            version=version,
            page_action=page_action,
            min_score=min_score,
            invisible=invisible,
            enterprise=enterprise,
            s=s_token,
            cdata=cdata,
            proxy=proxy,
            user_agent=user_agent,
        )
        wait = WaitOptions(timeout=timeout, polling_interval=polling_interval)
        solution = await client.solve(info, wait_options=wait)
    finally:
        await client.aclose()
    return {"success": True, "solution": _solution_to_dict(solution)}


async def solve_on_page(
    agent: Any,
    browser_id: int | str | None = None,
    *,
    autofill: bool | None = None,
    timeout: float | None = None,
    polling_interval: float | None = None,
) -> dict[str, Any]:
    """Detect, solve, and optionally autofill every captcha on the active page."""
    settings = config_helper.build_settings(config_helper.load_config(agent))
    if autofill is None:
        autofill = bool(settings.get("autofill", True))

    runtime = await _get_runtime(agent)
    resolved = await _resolve_browser_id(runtime, browser_id)
    driver = A0PageDriver(runtime, resolved)
    client = build_client(settings)
    try:
        options = SolveOnPageOptions(
            autofill=bool(autofill),
            throw_on_error=False,
            timeout=timeout,
            polling_interval=polling_interval,
        )
        results = await client.solve_on_page(driver, options=options)
    finally:
        await client.aclose()

    serialized = []
    solved = 0
    for result in results:
        if result.solution is not None:
            solved += 1
        serialized.append(
            {
                "captcha_type": result.info.type.value,
                "website_key": result.info.website_key,
                "solved": result.solution is not None,
                "filled": result.filled,
                "token": result.solution.token if result.solution else None,
                "error": result.error,
            }
        )
    return {
        "success": True,
        "browser_id": resolved,
        "url": await driver.url(),
        "autofill": bool(autofill),
        "count": len(serialized),
        "solved_count": solved,
        "results": serialized,
    }


async def get_balance(agent: Any) -> dict[str, Any]:
    """Return the Capsolver account balance and packages."""
    settings = config_helper.build_settings(config_helper.load_config(agent))
    client = build_client(settings)
    try:
        balance = await client.get_balance()
    finally:
        await client.aclose()
    return {"success": True, "balance": balance.balance, "packages": balance.packages}


def get_supported_captchas() -> dict[str, Any]:
    """List the captcha families this plugin can solve."""
    return {
        "success": True,
        "captcha_types": sorted(TOKEN_CAPTCHA_TYPES),
        "modes": {
            "token": "solve_captcha",
            "detect": "detect_captchas",
            "detect_and_solve": "solve_on_page",
        },
    }
