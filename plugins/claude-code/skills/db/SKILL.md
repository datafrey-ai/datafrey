---
name: db
description: Query connected databases using natural language. Use when the user wants to ask questions about their data, run queries, explore database schemas, or work with SQL.
allowed-tools: mcp__plugin_datafrey_datafrey__run
---

# DataFrey Database Skill

Query connected databases using natural language.

## Arguments

`$ARGUMENTS` is the user's natural language question or command.

## Workflow

1. Write SQL based on the user's question
2. Use the `run` tool to execute the SQL
3. Format query results as a readable table when possible

## Examples

- `/datafrey:db show me top 10 customers by revenue`
- `/datafrey:db how many orders were placed last month`
- `/datafrey:db list all tables`

## Instructions

- Always show the SQL before executing with `run`
- If the query looks destructive or unexpected, ask the user to confirm before running
- Format large result sets as tables; summarize if results exceed reasonable length
- Authentication is handled automatically — the user will be prompted in their browser on first use
