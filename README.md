# Capsolver for Agent Zero

An [Agent Zero](https://github.com/agent0ai/agent-zero) plugin that lets Agent
Zero solve captchas while browsing the web, using the
[Capsolver](https://capsolver.com) API.

Bring your own Capsolver API key — the plugin never ships a key.

## What it does

- **Detect** captchas on the page Agent Zero already has open.
- **Solve** reCAPTCHA v2, reCAPTCHA v3, and Cloudflare Turnstile.
- **Auto-solve** a whole page in one call: detect, solve, and (optionally) fill
the token back into the form.
- **Check balance** and list supported captcha types.

The plugin solves captchas **inside Agent Zero's own browser session** (the same
tab the `browser` tool controls). There is no second headless browser, so the
solved token is injected into the live page the agent is using.

## Requirements

- Agent Zero with the built-in **browser** plugin enabled.
- A Capsolver account and API key: <https://dashboard.capsolver.com>.

## Install

### From the Plugin Hub

Search for **Capsolver** in the Agent Zero Plugin Hub and install it.

### From Git

In the Agent Zero UI, open **Plugins → Install → From Git** and paste:

```
https://github.com/HenryJia/capsolver-a0
```

Installation runs the plugin's `hooks.py`, which installs the
[`capsolver-core`](https://pypi.org/project/capsolver-core/) SDK into the Agent
Zero framework runtime automatically. No manual `pip install` is required.

## Configure your API key

1. Open **Settings → Agent → Capsolver**.
2. Paste your Capsolver API key into **API Key**.
3. Click **Test Connection** to confirm the key works and see your balance.
4. Save.

Alternatively, leave the field empty and set the environment variable instead
(useful for headless / server deployments):

```bash
export CAPSOLVER_API_KEY="CAP-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Settings are resolved in this order: the key in the plugin settings wins,
otherwise `CAPSOLVER_API_KEY` is used.

## Usage

The plugin exposes a `capsolver` tool to the agent. You normally do not call it
directly — just ask Agent Zero to solve a captcha, and it will use the tool. The
agent-facing contract lives in
[`prompts/agent.system.tool.capsolver.md`](prompts/agent.system.tool.capsolver.md).

### Actions

| Action | API key needed | Description |
|---|---|---|
| `detect` | No | Scan the active browser tab and report captcha widgets. |
| `solve` | Yes | Token mode: solve from `captcha_type` + `website_url` + `website_key`. |
| `solve_on_page` | Yes | Detect, solve, and (by default) autofill every captcha on the active tab. |
| `balance` | Yes | Report account balance and packages. |
| `supported` | No | List captcha types this plugin can solve. |

### Example: auto-solve the current page

```json
{
  "tool_name": "capsolver",
  "tool_args": { "action": "solve_on_page" }
}
```

### Example: token mode

```json
{
  "tool_name": "capsolver",
  "tool_args": {
    "action": "solve",
    "captcha_type": "reCaptchaV2",
    "website_url": "https://example.com/login",
    "website_key": "6Le-wvkSAAAAAPBMRT..."
  }
}
```

Supported `captcha_type` values: `reCaptchaV2`, `reCaptchaV3`, `cloudflare`.

## Settings reference

| Setting | Default | Description |
|---|---|---|
| `api_key` | `""` | Capsolver API key. Falls back to `CAPSOLVER_API_KEY`. |
| `service` | `https://api.capsolver.com` | API endpoint (change only for a proxy/mirror). |
| `request_timeout` | `30` | Per-request HTTP timeout, seconds. |
| `default_timeout` | `120` | Max seconds to wait for a solution. |
| `polling_interval` | `5` | Seconds between polling attempts. |
| `autofill` | `true` | Write solved tokens back into the page for `solve_on_page`. |

## How it works

The plugin depends on the low-level
[`capsolver-core`](https://github.com/capsolver-ai/capsolver-core) SDK and adds a
thin Agent Zero integration layer:

```
tools/capsolver.py        Agent-facing tool (actions, JSON responses)
helpers/solver.py         High-level operations, error shaping
helpers/page_driver.py    Bridges Agent Zero's browser tab -> capsolver-core PageDriver
helpers/client.py         Builds a configured capsolver-core client
helpers/config.py         Plugin settings + env fallback
hooks.py                  Installs/removes capsolver-core (framework runtime)
api/capsolver_test.py     Settings "Test Connection" endpoint
webui/config.html         Settings UI
prompts/agent.system.tool.capsolver.md   Tool contract for the model
```

Unlike the reference [`capsolver-agent`](https://github.com/capsolver-ai/capsolver-agent)
package, which launches its own Playwright browser, this plugin reuses Agent
Zero's browser runtime. See [docs/architecture.md](docs/architecture.md) for
details.

## Development

```bash
# Run the test suite (uses the Agent Zero framework runtime)
/opt/venv-a0/bin/python -m pytest tests -q
```

The suite covers config normalization, the page-driver adapter, and browser
resolution without needing network access or a live browser.

See [docs/development.md](docs/development.md) for the local development
workflow and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT — see [LICENSE](LICENSE).
