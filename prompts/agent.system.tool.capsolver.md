### capsolver
Solve captchas on web pages using the Capsolver API. Works with the pages already open in Agent Zero's browser tool, so the solved token is injected into the same live session the agent is using. Requires a Capsolver API key (Settings > Agent > Capsolver, or the `CAPSOLVER_API_KEY` environment variable).

Supported captcha families: `reCaptchaV2`, `reCaptchaV3`, `cloudflare` (Cloudflare Turnstile).

Actions:
- `detect`: scan the active browser tab and report captcha widgets found (no API key needed). Optional `browser_id`.
- `solve`: token mode — solve from `captcha_type`, `website_url`, and `website_key` and return the token. Use when you already have the site parameters.
- `solve_on_page`: one-shot — detect, solve, and (by default) autofill every captcha on the active tab. Optional `browser_id`, `autofill`, `timeout`, `polling_interval`.
- `balance`: report the Capsolver account balance and packages.
- `supported`: list captcha types this plugin can solve.

Rules:
- Open the target page with the `browser` tool first; `detect` and `solve_on_page` act on the active tab (or `browser_id` when given).
- Prefer `solve_on_page` when the agent is already on the captcha page; it detects site keys automatically and injects the token.
- Use `solve` only when you already know the captcha type, page URL, and site key.
- Tokens expire; solve close to when the form is submitted.

Example — auto-solve on the current page:
~~~json
{
  "thoughts": ["The login page shows a reCAPTCHA; I'll auto-solve it on the open tab."],
  "headline": "Solving captcha on page",
  "tool_name": "capsolver",
  "tool_args": {
    "action": "solve_on_page"
  }
}
~~~

Example — token mode:
~~~json
{
  "thoughts": ["I know the site key, so I'll fetch a token directly."],
  "headline": "Solving captcha token",
  "tool_name": "capsolver",
  "tool_args": {
    "action": "solve",
    "captcha_type": "reCaptchaV2",
    "website_url": "https://example.com/login",
    "website_key": "6Le-wvkSAAAAAPBMRT..."
  }
}
~~~
