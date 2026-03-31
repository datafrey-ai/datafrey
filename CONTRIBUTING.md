# Contributing to DataFrey

Thank you for your interest in contributing to DataFrey. We welcome contributions from the community and are glad you are here.

## Getting started

DataFrey is a Python monorepo managed with [uv](https://docs.astral.sh/uv/) workspaces. You will need Python 3.13+ and uv installed.

1. Fork the repository on GitHub.

2. Clone your fork locally:

   ```bash
   git clone https://github.com/<your-username>/datafrey.git
   cd datafrey
   ```

3. Install dependencies:

   ```bash
   uv sync
   ```

4. Verify everything is working:

   ```bash
   uv run pytest
   ```

## Development workflow

1. Create a new branch from `main`:

   ```bash
   git checkout -b your-branch-name
   ```

2. Make your changes.

3. Run the test suite:

   ```bash
   uv run pytest
   ```

4. Format and lint your code:

   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   ```

5. Commit your changes and push to your fork.

## Project structure

The repository is organized as a uv workspace with four packages under `packages/`:

| Package | Description |
|---|---|
| `datafrey-cli` | The main CLI. Entry point for end users to set up database connections and manage MCP credentials. Published as `datafrey` on PyPI. |
| `datafrey-api` | Shared Pydantic models and API schema used across all packages. |
| `datafrey-mcp` | MCP server that bridges AI assistants to your databases via the DataFrey API. |
| `datafrey-mock` | Mock API server for local development and testing. |

The root `pyproject.toml` defines the workspace and shared dev dependencies (pytest, ruff).

## Pull request process

1. **Open an issue first** for non-trivial changes. This lets us discuss the approach before you invest time writing code. Small bug fixes and documentation improvements can go straight to a PR.

2. Create a branch with a descriptive name (e.g. `fix-connection-timeout`, `add-mysql-support`).

3. Write or update tests for your changes.

4. Ensure all tests pass and the code is formatted:

   ```bash
   uv run pytest
   uv run ruff format --check .
   uv run ruff check .
   ```

5. Open a pull request against the `main` branch. Include:
   - A clear description of what changed and why.
   - A link to the related issue, if applicable.
   - Any manual testing you performed.

6. A maintainer will review your PR. We may suggest changes. Once approved, a maintainer will merge it.

## Code style

- We use [ruff](https://docs.astral.sh/ruff/) for both formatting and linting.
- Follow the patterns and conventions already established in the codebase.
- Keep functions focused and files reasonably sized.
- Write clear docstrings for public APIs.
- Prefer explicit over implicit.

## Reporting bugs

Please use [GitHub Issues](https://github.com/datafrey-ai/datafrey/issues) to report bugs. A good bug report includes:

- A clear and descriptive title.
- Steps to reproduce the issue.
- Expected behavior and actual behavior.
- Your environment (OS, Python version, DataFrey version).
- Any relevant logs or error messages.

## Feature requests

Feature requests are welcome. Please open a [GitHub Issue](https://github.com/datafrey-ai/datafrey/issues) describing the use case and the behavior you would like to see. We will discuss feasibility and approach before implementation begins.

## Security

If you discover a security vulnerability, **do not open a public issue**. Please follow the process described in [SECURITY.md](SECURITY.md).

## License

By contributing to DataFrey, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE), the same license that covers this project.
