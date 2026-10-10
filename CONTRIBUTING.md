# Contributing

Thanks for your interest in improving the Capsolver plugin for Agent Zero!

## Getting set up

See [docs/development.md](docs/development.md) for runtimes, local plugin
installation, tests, and a live smoke test.

## Before you open a PR

1. Run the tests:

   ```bash
   /opt/venv-a0/bin/python -m pytest tests -q
   ```

2. Compile the Python you touched:

   ```bash
   /opt/venv-a0/bin/python -m py_compile hooks.py helpers/*.py tools/*.py api/*.py
   ```

3. If you changed detection/solving, run the detection smoke test in
   [docs/development.md](docs/development.md).

4. Update documentation when behavior, settings, or the tool contract changes:
   - [README.md](README.md) for user-facing changes.
   - [docs/architecture.md](docs/architecture.md) for design changes.
   - `prompts/agent.system.tool.capsolver.md` when tool actions/args change.

## Guidelines

- Keep the plugin small and focused; it should not duplicate Agent Zero's
  browser stack.
- Never commit secrets, API keys, or `.env` files. The default key is empty.
- Use fully qualified plugin imports (`usr.plugins.capsolver...`); no `sys.path`
  hacks.
- Return user-facing errors as JSON from the tool rather than raising.
- Follow the existing code style (type hints, docstrings, small functions).
- Add or update tests for logic you change.

## Reporting issues

Include:

- Agent Zero version and how the plugin was installed (Hub/Git/ZIP).
- The captcha family and page (or a minimal repro).
- The tool output/error (redact your API key).
- Whether `detect` works (it needs no API key), which isolates detection vs.
  solving problems.

## Security

Do not paste API keys into issues or PRs. If you believe you found a security
issue, report it privately rather than in a public issue.
