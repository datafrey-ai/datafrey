# DataFrey

[![PyPI version](https://img.shields.io/pypi/v/datafrey?style=flat-square)](https://pypi.org/project/datafrey/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](LICENSE)

MCP server for your database.

- **Vibecode SQL.** Ask, clean, and transform your data in Claude Code.
- **5 min setup.** Connect Snowflake and install the Claude Code plugin using the CLI.
- **Understands your data.** Solve complex problems using the planning agent.

[Documentation](https://docs.datafrey.ai) · [Website](https://datafrey.ai) · [GitHub](https://github.com/datafrey-ai/datafrey)

## Install

```bash
pip install datafrey
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install datafrey
```

Then run the CLI to log in, connect your database, and install the Claude Code plugin:

```bash
datafrey
```

Full walkthrough: [Quickstart](https://docs.datafrey.ai/quickstart). Learn more at [docs.datafrey.ai](https://docs.datafrey.ai).

---

## Commands

See the full [CLI reference](https://docs.datafrey.ai/reference/cli) for all commands and options.

| Command | Description |
| --- | --- |
| `datafrey login` | Authenticate with DataFrey |
| `datafrey logout` | Remove stored credentials |
| `datafrey status` | Show auth, database, and index status |
| `datafrey db connect` | Connect a new database (interactive) |
| `datafrey db list` | List connected databases |
| `datafrey db drop` | Remove the connected database |
| `datafrey index` | Sync the database schema index |
| `datafrey index drop` | Drop the database schema index |
| `datafrey client` | Set up an AI client (interactive) |
| `datafrey client claude` | Configure Claude Code |
| `datafrey client cursor` | Configure Cursor |
| `datafrey client mcp` | Print MCP config block for any MCP-compatible client |
| `datafrey doctor` | Check environment and connectivity |

---

## Supported databases

- **Snowflake** -- fully supported

More databases are coming soon. [Request a database](https://github.com/datafrey-ai/datafrey/issues/new) if yours is not listed.

---

## Packages

This repository is a Python monorepo managed with [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/). The main entry point is the `datafrey` CLI package.

| Package | PyPI | Description |
| --- | --- | --- |
| [`datafrey-cli`](packages/datafrey-cli/) | [![PyPI](https://img.shields.io/pypi/v/datafrey?style=flat-square&label=datafrey)](https://pypi.org/project/datafrey/) | CLI for managing databases and MCP setup |
| [`datafrey-api`](packages/datafrey-api/) | [![PyPI](https://img.shields.io/pypi/v/datafrey-api?style=flat-square&label=datafrey-api)](https://pypi.org/project/datafrey-api/) | Shared Pydantic models for the API |
| [`datafrey-mcp`](packages/datafrey-mcp/) | [![PyPI](https://img.shields.io/pypi/v/datafrey-mcp?style=flat-square&label=datafrey-mcp)](https://pypi.org/project/datafrey-mcp/) | MCP server bridge |
| [`datafrey-mock`](packages/datafrey-mock/) | [![PyPI](https://img.shields.io/pypi/v/datafrey-mock?style=flat-square&label=datafrey-mock)](https://pypi.org/project/datafrey-mock/) | Mock API server for local development |

---

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/datafrey-ai/datafrey.git
cd datafrey
uv sync
uv run pytest
```

Format and lint:

```bash
uv run ruff format packages/
uv run ruff check packages/
```

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

For security vulnerabilities, do not open a public issue. Instead, email [slava+security@datafrey.ai](mailto:slava+security@datafrey.ai). See [SECURITY.md](SECURITY.md) for details.

---

## Telemetry

DataFrey sends usage events from the CLI and the MCP server to help us improve the product. Events are linked to your DataFrey account via your WorkOS user ID (`sub`) after login — a pseudonymous identifier, not your email.

**CLI** — command name, outcome, duration, error class, provider type (e.g. `snowflake`), auth method, CLI version, OS, architecture, Python version, CI flag.

**MCP server** — session start (with the MCP client name, e.g. `claude-ai`, `cursor`), tool name (`plan` or `run`), outcome, duration, and error class.

**Never collected (anywhere):** email, name, credentials, hostnames, account/user/role/warehouse/database names, file paths, env vars, error messages, IP addresses, prompt content, SQL, query results, or any tool arguments / responses.

**Opt out** by setting either:

```bash
export DATAFREY_TELEMETRY_DISABLED=1
export DO_NOT_TRACK=1
```

The same variables disable telemetry for both the CLI and the MCP server (set them in the MCP server's environment if you self-host). When opted out, no events are sent and no telemetry identifiers are written to your local config.

---

## License

Apache 2.0 -- see [LICENSE](LICENSE) for details.

Copyright 2025-2026 DataFrey, Inc.
