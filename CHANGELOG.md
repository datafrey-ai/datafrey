# Changelog

All notable changes to this project will be documented in this file.

## [0.3.1] - 2026-04-19

### Fixed

- `datafrey client claude` next-step hint now shows the namespaced MCP server name (`/mcp enable plugin:datafrey:datafrey`) so the command actually matches the plugin-bundled server.

## [0.3.0] - 2026-04-18

### Added

- `datafrey client` command group with `claude`, `cursor`, and `mcp` subcommands for installing AI-client configs from one menu.
- `datafrey index drop` to remove the local index.
- Live indexing progress inside `datafrey status` and a hint after `datafrey index` starts.
- Prompt to index the schema immediately after a successful `db connect`.
- Auto-generated connection name and auto-selected single-option auth during `db connect`; auth prompt now shown before the browser opens.
- Opt-out PostHog telemetry in CLI and MCP server.

### Changed

- Running `datafrey` with no subcommand launches login directly.
- `datafrey status` folds in index status; `datafrey index` goes straight to sync.
- Claude Code setup installs the marketplace plugin instead of patching `mcp add`; MCP enable instruction corrected to reference the `/mcp` slash command.
- Cursor integration switched from file-patching to a deep-link install.
- When already logged in, the CLI prompts to re-authenticate instead of exiting.
- Snowflake-only: the unfinished Postgres connector was removed; RSA Key Pair auth hidden from the UI until tested.
- Snowflake SQL hint snippets highlighted in cyan; inline SQL hint styling made consistent.
- Removed `docs.datafrey.ai` links from CLI output.
- README rewritten: quick start, "how it works" as a four-step user flow, and updated commands.

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
