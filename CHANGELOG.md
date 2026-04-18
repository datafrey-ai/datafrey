# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-04-18

### Added

- `datafrey client` — install Claude Code / Cursor / generic MCP configs from one menu.
- `datafrey index drop` — remove the local index.
- Live indexing progress inside `datafrey status`; prompt to index after `db connect`.
- Opt-out PostHog telemetry in CLI and MCP server.
- Auto-generate a connection name and auto-select the single available auth option during `db connect`.

### Changed

- Running `datafrey` with no subcommand now launches login.
- `datafrey status` folds in index status; `datafrey index` is a direct command.
- Claude Code setup uses marketplace plugin install instead of patching `mcp add`.
- When already logged in, prompt to re-login instead of exiting.
- Snowflake-only: the unfinished Postgres connector was removed.

### Security

- Keyring backend allow-list (OS-native only); reject third-party fallbacks.
- Atomic config writes; refuse symlinks and non-owner files; enforce 0o600.
- Sanitize server error strings (strip ANSI, bound length, escape Rich markup).
- Roll back access token if refresh-token write fails.
- Publish workflow: SHA-pin actions, validate tag version, pass inputs via env.
- Tighten dependency upper bounds across all packages; add Dependabot.

## [0.2.0] - 2026-04-08

### Added

- **Planning skill** — the `/db` skill now intelligently decides when to call `plan` before running a query. Complex or ambiguous questions go through a planning step; simple ones execute directly.
- **`datafrey index sync`** — builds a database index used by the planning skill. Run this after onboarding and whenever your schema changes. Planning will not work without it.
- **`datafrey index status`** — shows index status: last synced, table count, column count.

### Changed

- MCP server now exposes `plan` and `run` tools (previously only `run`).

## [0.1.1] - 2026-04-04

### Added

- Claude Code plugin (`claude plugin marketplace add datafrey-ai/datafrey`).

## [0.1.0] - 2026-04-01

### Added

- Initial release: CLI, MCP server, and Snowflake support.
