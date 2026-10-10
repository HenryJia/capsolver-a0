# Development

How to work on this plugin locally.

## Runtimes

Agent Zero has two Python runtimes:

| Runtime | Path | Use for |
|---|---|---|
| Framework | `/opt/venv-a0/bin/python` | Plugin code, hooks, tests, backend |
| Task | `/opt/venv/bin/python` | Unrelated task code |

This plugin always targets the **framework** runtime. `hooks.py` installs
`capsolver-core` there.

## Local plugin install

The plugin lives in this repository but Agent Zero loads custom plugins from
`usr/plugins/<name>`. Symlink it for live development:

```bash
ln -sfn /a0/usr/projects/capsolver_plugin_for_agent_zero /a0/usr/plugins/capsolver
```

The manifest `name` (`capsolver`) must match the directory name Agent Zero sees.

## Run the tests

```bash
/opt/venv-a0/bin/python -m pytest tests -q
```

`conftest.py` puts the Agent Zero root on `sys.path` so imports like
`usr.plugins.capsolver.helpers.solver` and `plugins._browser.helpers.selector`
resolve. `pytest.ini` uses `--import-mode=importlib` so the plugin's local
`helpers/` package does not shadow Agent Zero's framework `helpers/` package.

## Verify imports manually

```bash
cd /a0
/opt/venv-a0/bin/python -c "\
from usr.plugins.capsolver.helpers import config, client, page_driver, solver; \
print('ok', sorted(solver.TOKEN_CAPTCHA_TYPES))"
```

## Live smoke test (detection)

Detection needs a real browser tab but no API key. With the `_browser` plugin
enabled:

```bash
cd /a0
PYTHONPATH=/a0 /opt/venv-a0/bin/python - <<'PY'
import asyncio
from plugins._browser.helpers.runtime import get_runtime
from usr.plugins.capsolver.helpers.page_driver import A0PageDriver
from capsolver_core import Capsolver

async def main():
    runtime = await get_runtime("smoke-detect")
    opened = await runtime.call("open", "https://www.google.com/recaptcha/api2/demo")
    bid = opened["id"]
    driver = A0PageDriver(runtime, bid)
    client = Capsolver(api_key="unused")
    infos = await client.get_captcha_info(driver)
    await client.aclose()
    print([i.type.value for i in infos], [i.website_key for i in infos])
    await runtime.call("close_browser", bid)

asyncio.run(main())
PY
```

Expected: `['reCaptchaV2']` and the demo site key.

## Live solve test (needs a key)

Set `CAPSOLVER_API_KEY` and call `solve_on_page` against a real page. This spends
account balance, so use a test key and a cheap target.

## Code map

| File | Responsibility |
|---|---|
| `hooks.py` | Install/uninstall `capsolver-core` in the framework runtime. |
| `helpers/config.py` | Load + normalize plugin settings and env fallback. |
| `helpers/client.py` | Build a configured `capsolver-core` client; missing-key error. |
| `helpers/page_driver.py` | Adapt an Agent Zero tab to the `PageDriver` protocol. |
| `helpers/solver.py` | High-level operations used by the tool. |
| `tools/capsolver.py` | Agent-facing tool: action dispatch + JSON responses. |
| `api/capsolver_test.py` | Settings "Test Connection" endpoint. |
| `webui/config.html` + `webui/capsolver-config-store.js` | Settings UI. |
| `prompts/agent.system.tool.capsolver.md` | Tool contract for the model. |

## Conventions

- Plugin-local imports use the fully qualified `usr.plugins.capsolver...` path.
- No `sys.path` hacks and no symlink-based imports.
- User-facing errors are returned as JSON, not raised to the framework.
- Keep the tool prompt in sync with the actions in `tools/capsolver.py`.

## Testing checklist before committing

1. `py_compile` all Python files.
2. `pytest tests -q` passes.
3. Plugin loads: `plugins.get_plugin_meta("capsolver")` is not `None`.
4. Tool class loads: `extract_tools.load_classes_from_file(..., Tool)` finds
   `Capsolver`.
5. Detection smoke test (above) returns the expected captcha type.
