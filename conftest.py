"""Test bootstrap for the Capsolver plugin.

The plugin imports framework modules (``helpers.*``, ``plugins._browser.*``) and
its own code as ``usr.plugins.capsolver.*``. Those live under the Agent Zero
root, so make sure it is importable when running the suite from anywhere.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_a0_root_on_path() -> None:
    candidates = []
    env_root = os.environ.get("A0_ROOT", "").strip()
    if env_root:
        candidates.append(Path(env_root))
    # <root>/usr/projects/<project>/conftest.py -> <root> is four levels up
    candidates.append(Path(__file__).resolve().parents[3])
    candidates.append(Path("/a0"))
    for candidate in candidates:
        if (candidate / "helpers" / "tool.py").is_file() and (candidate / "usr").is_dir():
            root = str(candidate)
            if root not in sys.path:
                sys.path.insert(0, root)
            return


_ensure_a0_root_on_path()
