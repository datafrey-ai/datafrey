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

### 2. Log in

```bash
datafrey login
```

The CLI walks you through authentication, connecting your database, and configuring MCP — all in one flow.

Then ask anything with `/db` in Claude Code.

### Claude Code plugin

Install the plugin directly from this repo:

```
claude plugin marketplace add datafrey-ai/datafrey
claude plugin install datafrey@datafrey
```

See the [plugin docs](https://docs.datafrey.ai) for details.

---

## How it works

DataFrey connects your database to AI assistants securely:

1. **Authenticate** -- `datafrey login` opens your browser for OAuth login via WorkOS. Tokens are stored in your OS keychain — never in plaintext on disk.

2. **Connect** -- Your credentials are encrypted client-side using AES-256-GCM + RSA-OAEP before they leave your machine and stored server-side in a dedicated secrets vault with per-tenant isolation.

3. **Index** -- `datafrey index sync` analyzes your connected database and builds an index used by the planning skill. Run it after onboarding and whenever your schema changes.

4. **Query** -- Use `/db` in Claude Code to ask questions in natural language. Simple queries run directly; complex questions go through a planning step that uses the index to produce accurate results.

---

## Commands

`datafrey login` is all you need to get started. For more control, additional commands are available:

| Command | Description |
| --- | --- |
| `datafrey login` | Authenticate and set everything up |
| `datafrey db connect` | Connect a database manually |
| `datafrey db list` | List connected databases |
| `datafrey db drop` | Remove a connected database |
| `datafrey index sync` | Build or refresh the column index (required for planning) |
| `datafrey index status` | Show index status (tables, columns, last indexed) |
| `datafrey mcp setup` | Configure a specific AI client for MCP |
| `datafrey doctor` | Check environment and connectivity |
| `datafrey status` | Show current auth status |

See the [documentation](https://docs.datafrey.ai) for the full reference.

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
