# Architecture

This document explains how the Capsolver plugin integrates with Agent Zero and
why it is built the way it is.

## Goals

- Let Agent Zero solve captchas on pages it is already browsing.
- Keep the solved token in the **same** browser session the agent is using.
- Require only a user-supplied Capsolver API key.
- Stay small: no duplicated browser stack, no bundled secrets.

## Design decision: reuse Agent Zero's browser

The reference [`capsolver-agent`](https://github.com/capsolver-ai/capsolver-agent)
package solves captchas by launching its own headless Playwright browser. That is
fine for a standalone tool, but inside Agent Zero it is wasteful and fragile:

- A second browser has no access to the cookies/session of the tab the agent is
  actually interacting with.
- Autofilling a token into a *different* browser instance does not help the agent
  submit the form it is looking at.
- It duplicates browser lifecycle, proxy, and profile handling that Agent Zero's
  `_browser` plugin already owns.

So this plugin depends on the low-level
[`capsolver-core`](https://github.com/capsolver-ai/capsolver-core) SDK (detection
JS, task building, polling) and bridges it to Agent Zero's browser runtime.

```
             +-----------------------------+
             |  tools/capsolver.py (Tool)  |
             +--------------+--------------+
                            |
             +--------------v--------------+
             |      helpers/solver.py      |  high-level ops + error shaping
             +----+--------------------+---+
                  |                    |
     +------------v------+   +---------v----------+
     | helpers/client.py |   | helpers/page_driver |
     | (capsolver-core)  |   |  A0PageDriver       |
     +-------------------+   +---------+----------+
                                       |
                            +----------v-----------+
                            | Agent Zero browser   |
                            | runtime (_browser)   |
                            +----------------------+
```

## The page-driver bridge

`capsolver-core` works against a tiny page interface (a `PageDriver` protocol):

```python
async def evaluate(script, arg=None) -> Any
async def url() -> str
async def wait_for_selector(selector, *, timeout=None) -> None
```

Agent Zero's browser runtime exposes a different surface:

```python
await runtime.call("evaluate", browser_id, script)  # -> {"result": ..., "state": ...}
await runtime.call("state", browser_id)             # -> {"currentUrl": ..., ...}
```

`helpers/page_driver.py` adapts one to the other:

- `url()` reads `state.currentUrl`.
- `evaluate(script, arg)` turns the function snippet into an immediately-invoked
  expression `(script)(arg)` because Agent Zero's `evaluate` accepts only a
  script string, then unwraps the `result` field.
- Agent Zero evaluates in the page's **main world**, which is required to read
  widget globals such as `window.___grecaptcha_cfg`.
- `wait_for_selector` is a no-op; detection and solving do not need it and Agent
  Zero has no portable wait primitive.

Because Agent Zero owns the browser, `browser_id` resolution defaults to the last
interacted tab and accepts an explicit `browser_id` for multi-tab workflows.

## Request flow (solve_on_page)

1. The agent calls the `capsolver` tool with `action: "solve_on_page"`.
2. `tools/capsolver.py` dispatches to `helpers/solver.solve_on_page`.
3. The solver resolves the target tab via the browser runtime.
4. An `A0PageDriver` wraps that tab.
5. `capsolver-core` runs its detection JS through the driver to find site keys.
6. `capsolver-core` calls the Capsolver API (`createTask` + poll `getTaskResult`)
   using the configured key.
7. `capsolver-core` injects the solved token back into the page via the driver.
8. The solver returns a JSON summary; the tool records it in history.

## Configuration and secrets

- The API key is read from plugin settings first, then `CAPSOLVER_API_KEY`.
- Settings are stored through Agent Zero's standard plugin-config mechanism
  (`config.json`), which supports global / project / agent-profile scoping.
- The key is never committed and never bundled. `default_config.yaml` ships an
  empty key.
- `helpers/config.build_settings` normalizes raw config into typed values so the
  rest of the code never deals with strings-vs-numbers ambiguity.

## Lifecycle

`hooks.py` runs in the Agent Zero framework runtime:

- `install()` ensures `capsolver-core` is importable, installing it if needed.
- `pre_update()` is a no-op (no owned processes).
- `uninstall()` removes `capsolver-core`, which this plugin exclusively owns.

No `execute.py` is provided: there is no manual setup step.

## Error handling

- Missing API key -> `missing_api_key` error with an actionable message.
- Invalid arguments -> `invalid_argument`.
- API/network failures -> returned as a JSON error with the exception type, so
  the model can decide whether to retry.
- Detection works without an API key, so `detect` is always usable for
  troubleshooting.

## Extending

- **More captcha types:** add the family to `TOKEN_CAPTCHA_TYPES` in
  `helpers/solver.py` and to the tool prompt. `capsolver-core` may need a handler
  for the new type; if so, extend the SDK rather than this plugin.
- **New actions:** add a branch in `tools/capsolver.py::_dispatch` and a solver
  function.
- **Proxy support:** `solve` already forwards a `proxy` argument; expose it in
  the UI if you want a persistent proxy setting.
