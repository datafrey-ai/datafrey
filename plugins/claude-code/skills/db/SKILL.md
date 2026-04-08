---
name: db
description: Query connected databases using natural language. Use when the user wants to ask questions about their data, run queries, explore database schemas, or work with SQL.
allowed-tools: mcp__plugin_datafrey_datafrey__plan, mcp__plugin_datafrey_datafrey__run
---

# DataFrey Database Skill

Query connected databases using natural language.

## Arguments

`$ARGUMENTS` is the user's natural language question or command.

## Tools

- `plan` — generates a query plan from a natural language prompt using the database index. Use when the right SQL is not immediately obvious.
- `run` — executes SQL against the connected database.

## Workflow

Choose based on how clear the SQL is:

**When the SQL is obvious** (e.g. `list all tables`, `count rows in orders`, simple aggregations on known tables):
1. Write the SQL directly
2. Show it to the user
3. Execute with `run`

**When the SQL is not obvious** (e.g. unfamiliar schema, complex joins, ambiguous column names, analytical questions):
1. Call `plan` with the user's question — it uses the database index to produce a verified query plan
2. Show the plan and the SQL it implies
3. Execute with `run`

## Examples

- `/datafrey:db show me top 10 customers by revenue`
- `/datafrey:db how many orders were placed last month`
- `/datafrey:db list all tables`

## Instructions

- Always show the SQL before executing with `run`
- If the query looks destructive or unexpected, ask the user to confirm before running
- Format large result sets as tables; summarize if results exceed reasonable length
- Authentication is handled automatically — the user will be prompted in their browser on first use
- `plan` requires the database index to be built — if it fails with an index error, tell the user to run `datafrey index sync`
