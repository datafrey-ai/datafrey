# Datafrey Plugin for Claude Code

Query connected databases with natural language. Run SQL, explore schemas, and analyze data.

## Installation

```
claude plugin marketplace add datafrey-ai/datafrey
claude plugin install datafrey@datafrey
```

## What it provides

- **MCP Server** — connects to the Datafrey API at `https://mcp.datafrey.ai/mcp`
- **`/datafrey:db` command** — run SQL queries against your connected databases

## Usage

```
/datafrey:db show me top 10 customers by revenue
/datafrey:db how many orders were placed last month
/datafrey:db list all tables
```

> Note: Plugin commands are namespaced as `/datafrey:db`. For a shorter `/db` alias, add the skill directly to your project's `.claude/skills/` directory.

## Prerequisites

- A Datafrey account with at least one connected database
- Sign up at [datafrey.ai](https://datafrey.ai)

## Authentication

No separate login needed. On first use, Claude Code opens your browser for OAuth login via WorkOS. Tokens are managed automatically after that.

## MCP for other AI tools

This plugin is Claude Code specific. The underlying MCP server works with any MCP-compatible client (Cursor, Claude Desktop, Codex, etc.). Use the CLI to configure those:

```
pip install datafrey
datafrey client
```

## License

Apache-2.0
