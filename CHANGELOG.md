# Changelog

All notable changes to this project will be documented in this file.

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
