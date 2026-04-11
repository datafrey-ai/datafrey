"""Root Typer app: login, logout, status, doctor, global error handler."""

from __future__ import annotations

import sys
from typing import Annotated, Optional

import typer

import datafrey
from datafrey.exceptions import DatafreyError
from datafrey.ui.console import console, err_console
from datafrey.ui.display import print_docs_link, print_error, print_success

app = typer.Typer(
    name="datafrey",
    help="Manage database connections and MCP servers.",
    invoke_without_command=True,
    add_completion=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"datafrey {datafrey.__version__}")
        raise typer.Exit()


@app.callback()
def _app_callback(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version.",
        ),
    ] = None,
) -> None:
    """Datafrey CLI — connect your database, query it from any AI."""
    _check_first_run()
    if ctx.invoked_subcommand is None:
        login()


def _check_first_run() -> None:
    """Show welcome panel on first invocation."""
    from datafrey.config import load_config, save_config

    config = load_config()
    if not config.get("first_run_complete"):
        from datafrey.ui.display import show_welcome_panel

        show_welcome_panel(datafrey.__version__)
        config["first_run_complete"] = True
        save_config(config)


# ── login ──


@app.command()
def login(
    no_browser: Annotated[
        bool, typer.Option("--no-browser", help="Don't open browser automatically.")
    ] = False,
) -> None:
    """Authenticate with Datafrey via browser."""
    from datafrey.auth import token_store
    from datafrey.auth.device_flow import start_device_flow

    # Already logged in?
    try:
        existing = token_store.get_access_token()
        if existing:
            relogin = typer.confirm("Already logged in. Re-login?", default=False)
            if not relogin:
                raise typer.Exit(0)
    except DatafreyError:
        pass  # Keyring issues — proceed with login

    result = start_device_flow(no_browser=no_browser)

    token_store.store_tokens(result["access_token"], result["refresh_token"])

    user = result.get("user", {})
    name = user.get("first_name", "")
    if user.get("last_name"):
        name = f"{name} {user['last_name']}".strip()
    email = user.get("email", "")
    identity = f"{name} ({email})" if name else email

    print_success(f"Logged in as {identity}")
    print_success(f"Token stored in {token_store.get_keyring_backend_name()}")

    from datafrey.cli.db import db_connect

    db_connect()


# ── logout ──


@app.command()
def logout() -> None:
    """Remove stored credentials."""
    from datafrey.auth import token_store

    token_store.clear_tokens()
    console.print("Logged out.")


# ── status / whoami ──


@app.command()
def status(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON.")
    ] = False,
) -> None:
    """Show authentication, database, and index status."""
    from datafrey.auth.middleware import get_authenticated_client
    from datafrey.ui.display import print_json_success, show_status

    with get_authenticated_client() as client:
        resp = client.get_status()
        databases = client.list_databases()
        db = databases[0] if databases else None
        index_status = None
        if db and db.status.value == "connected":
            try:
                index_status = client.get_index_status(db.id)
            except Exception:
                pass

    if json_output:
        data: dict = {
            "authenticated": True,
            "user": {"email": resp.user.email, "name": resp.user.name},
            "databases_count": resp.databases_count,
        }
        if db:
            data["database"] = {
                "name": db.name,
                "host": db.host,
                "status": db.status.value,
            }
        if index_status is not None:
            data["index"] = index_status.model_dump(mode="json")
        print_json_success(data)
    else:
        show_status(resp.user.email, resp.user.name, db, index_status)


@app.command(hidden=True)
def whoami(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON.")
    ] = False,
) -> None:
    """Alias for status."""
    status(json_output=json_output)


# ── doctor ──


@app.command()
def doctor() -> None:
    """Check environment and connectivity."""
    all_ok = True

    # Python version
    py_ver = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    if sys.version_info >= (3, 13):
        print_success(f"Python {py_ver}")
    else:
        print_error(f"Python {py_ver} (requires >=3.13)")
        all_ok = False

    # CLI version
    print_success(f"datafrey {datafrey.__version__}")

    # Keyring
    try:
        from datafrey.auth.token_store import (
            _check_keyring_backend,
            get_keyring_backend_name,
        )

        _check_keyring_backend()
        print_success(f"Secure keyring available ({get_keyring_backend_name()})")
    except DatafreyError as e:
        print_error(str(e))
        all_ok = False

    # Auth status
    try:
        from datafrey.auth.middleware import get_authenticated_client

        with get_authenticated_client() as client:
            resp = client.get_status()
            print_success(f"Authenticated as {resp.user.email}")

            # Database count
            if resp.databases_count > 0:
                print_success(f"{resp.databases_count} database(s) connected")
            else:
                err_console.print("[red]✗[/] No databases connected")
                err_console.print("  [dim]→ Run 'datafrey db connect' to add one.[/]")
                all_ok = False
    except DatafreyError:
        # Try just API reachability
        import httpx

        from datafrey.config import get_api_url

        try:
            url = get_api_url()
            httpx.get(url, timeout=2.0)
            print_success(f"API reachable ({url})")
        except Exception:
            err_console.print(f"[red]✗[/] API unreachable ({url})")
            all_ok = False
        err_console.print("[red]✗[/] Not authenticated")
        err_console.print("  [dim]→ Run 'datafrey login' to sign in.[/]")
        all_ok = False

    print_docs_link("troubleshooting")
    raise typer.Exit(0 if all_ok else 1)


# ── Register subgroups ──

from datafrey.cli.db import db_app  # noqa: E402
from datafrey.cli.index import index_command  # noqa: E402
from datafrey.cli.mcp import mcp_app  # noqa: E402

app.add_typer(db_app, name="db", help="Manage database connections.")
app.command("index", help="Sync the database schema index.")(index_command)
app.add_typer(mcp_app, name="mcp", help="Configure MCP clients.")


# ── Entry point with global error handling ──


def main() -> None:
    """Entry point for the datafrey CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print()
        raise SystemExit(130)
    except DatafreyError as e:
        print_error(str(e), e.hint)
        raise SystemExit(1)
