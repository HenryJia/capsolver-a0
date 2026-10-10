"""Lifecycle hooks for the Capsolver plugin.

These run inside the Agent Zero framework runtime. ``install`` makes sure the
``capsolver-core`` SDK is available; ``uninstall`` removes only dependencies
this plugin owns.
"""

from __future__ import annotations

import importlib
import importlib.util
import shutil
import subprocess
import sys

# Pinned to keep behaviour stable; bump deliberately after testing.
CAPSOLVER_CORE_REQUIREMENT = "capsolver-core>=0.1.1,<0.2"


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _pip_install(requirement: str) -> None:
    """Install a requirement into the framework runtime."""
    uv = shutil.which("uv")
    if uv:
        subprocess.check_call([uv, "pip", "install", "--python", sys.executable, requirement])
        return
    subprocess.check_call([sys.executable, "-m", "pip", "install", requirement])


def install() -> None:
    """Ensure the capsolver-core SDK is installed in the framework runtime."""
    if not _has_module("capsolver_core"):
        _pip_install(CAPSOLVER_CORE_REQUIREMENT)
        importlib.invalidate_caches()
        if not _has_module("capsolver_core"):
            raise RuntimeError(
                "capsolver-core is unavailable after installation; Capsolver plugin cannot load."
            )


def pre_update() -> None:
    """No owned processes to stop before an update."""
    return None


def uninstall() -> None:
    """Remove the plugin-owned dependency.

    ``capsolver-core`` is installed only for this plugin, so it is safe to
    remove. Shared packages and unrelated user data are left untouched.
    """
    if not _has_module("capsolver_core"):
        return
    uv = shutil.which("uv")
    if uv:
        subprocess.call([uv, "pip", "uninstall", "--python", sys.executable, "capsolver-core"])
        return
    subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", "capsolver-core"])
