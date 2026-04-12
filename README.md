<div align="center">

# DataFrey

**Ask your database from Claude Code.**

Smart MCP server for your database. Set up once, query anything.

[![PyPI version](https://img.shields.io/pypi/v/datafrey?style=flat-square)](https://pypi.org/project/datafrey/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](LICENSE)

[Documentation](https://docs.datafrey.ai) | [Website](https://datafrey.ai) | [GitHub](https://github.com/datafrey-ai/datafrey)

</div>

---

## Quick start

### 1. Install

```bash
pip install datafrey
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install datafrey
```

### 2. Connect your database

```bash
datafrey
```

The CLI walks you through authentication, connecting your database, indexing your schema, and configuring your AI client — all in one flow.

Then ask anything with `/db` in Claude Code.

---

## How it works

1. **Authenticate** — OAuth login via browser. Tokens are stored in your OS keychain, never in plaintext on disk.

2. **Connect** — Credentials are encrypted client-side (AES-256-GCM + RSA-OAEP) before leaving your machine and stored in a per-tenant secrets vault.

3. **Index** — The CLI analyzes your schema and builds a column index for the planning skill. This happens automatically during onboarding; re-run `datafrey index` whenever your schema changes.

4. **Query** — Use `/db` in Claude Code to ask questions in natural language. Simple queries run directly; complex ones go through a planning step that uses the index to produce accurate SQL.

---

## Commands

| Command | Description |
| --- | --- |
| `datafrey login` | Authenticate with Datafrey |
| `datafrey logout` | Remove stored credentials |
| `datafrey status` | Show auth, database, and index status |
| `datafrey db connect` | Connect a new database (interactive) |
| `datafrey db list` | List connected databases |
| `datafrey db drop` | Remove the connected database |
| `datafrey index` | Sync the database schema index |
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

For security vulnerabilities, do not open a public issue. Instead, email [slava+urgent@datafrey.ai](mailto:slava+urgent@datafrey.ai). See [SECURITY.md](SECURITY.md) for details.

---

## License

Apache 2.0 -- see [LICENSE](LICENSE) for details.

Copyright 2025-2026 DataFrey, Inc.
