"""db subgroup: connect, list, drop."""

from __future__ import annotations

from typing import Annotated

import typer

from datafrey.ui.console import console
from datafrey.ui.display import (
    print_hint,
    print_json_success,
    show_databases_table,
    show_review_panel,
)
from datafrey.ui.prompts import prompt_confirm

db_app = typer.Typer(no_args_is_help=True)


def _offer_index(db_id: str) -> None:
    """Ask user if they want to index schema; fire-and-forget if yes."""
    from datafrey.auth.middleware import get_authenticated_client
    from datafrey.telemetry import track
    from datafrey.telemetry.events import INDEX_OFFERED, INDEX_STARTED
    from datafrey.ui.display import print_success

    console.print()
    console.print(
        "Schema indexing lets the AI understand your database structure for better query planning."
    )
    accepted = prompt_confirm("Index schema now? (recommended)", default=True)
    track(INDEX_OFFERED, source="post_connect", accepted=accepted)
    if accepted:
        with get_authenticated_client() as client:
            client.reindex_database(db_id)
        track(INDEX_STARTED, source="post_connect")
        print_success("Indexing started.")
        print_hint("Run 'datafrey status' to check progress.")
    else:
        print_hint(
            "When ready, run 'datafrey index' to index. "
            "Planning won't work until schema is indexed."
        )
    console.print()


@db_app.command("list")
def db_list(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON.")
    ] = False,
) -> None:
    """List connected databases."""
    from datafrey.auth.middleware import get_authenticated_client

    with get_authenticated_client() as client:
        databases = client.list_databases()

    if json_output:
        print_json_success(
            {"databases": [d.model_dump(mode="json") for d in databases]}
        )
        return

    if not databases:
        console.print("No databases connected. Run 'datafrey db connect' to add one.")
        raise typer.Exit(0)

    show_databases_table(databases)
    print_hint("Run 'datafrey db drop' to remove the database.")


@db_app.command("drop")
def db_drop(
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation.")
    ] = False,
) -> None:
    """Remove the connected database."""
    from datafrey.auth.middleware import get_authenticated_client

    with get_authenticated_client() as client:
        databases = client.list_databases()
        if not databases:
            console.print("No databases connected.")
            raise typer.Exit(0)

        db = databases[0]
        if not yes:
            if not prompt_confirm(f'Remove "{db.name}"?', default=False):
                raise typer.Exit(0)

        client.delete_database(db.id)

    console.print("Database removed.")


@db_app.command("connect")
def db_connect() -> None:
    """Connect a new database (interactive)."""
    import time

    from datafrey.auth.middleware import get_authenticated_client
    from datafrey.cli.onboarding import (
        encrypt_and_submit,
        ensure_recent_auth,
        run_onboarding,
        wait_for_connection,
    )
    from datafrey.providers.base import get_provider, get_provider_choices
    from datafrey.telemetry import track
    from datafrey.telemetry.events import (
        DB_CONNECT_ABORTED,
        DB_CONNECT_AUTH_SELECTED,
        DB_CONNECT_CONNECTED,
        DB_CONNECT_CREDENTIALS_ENTERED,
        DB_CONNECT_FAILED,
        DB_CONNECT_PROVIDER_SELECTED,
        DB_CONNECT_REVIEW_SHOWN,
        DB_CONNECT_SETUP_COMPLETED,
        DB_CONNECT_STARTED,
        DB_CONNECT_SUBMITTED,
    )
    from datafrey.ui.prompts import prompt_select

    import datafrey.providers  # noqa: F401 — populates provider registry

    track(DB_CONNECT_STARTED)

    ensure_recent_auth()

    # Check limit before starting onboarding
    with get_authenticated_client() as client:
        databases = client.list_databases()
    if databases:
        from datafrey.ui.console import err_console

        err_console.print(
            "[bold red]Error:[/bold red] You already have a database connected. "
            "Remove it first with [bold]datafrey db drop[/bold]."
        )
        raise typer.Exit(1)

    # Select provider
    provider_name = prompt_select("Select database provider:", get_provider_choices())
    track(DB_CONNECT_PROVIDER_SELECTED, provider=provider_name)
    provider = get_provider(provider_name)

    # Auth method (auto-selects if only one option)
    console.print()
    partial_choices = provider.collect_auth_method()
    auth_method = partial_choices.get("auth_method", "unknown")
    track(DB_CONNECT_AUTH_SELECTED, provider=provider_name, auth_method=auth_method)

    # Offer to open provider console
    if provider_name == "snowflake":
        console.print()
        console.print(
            "You'll need to run some SQL queries as an admin to set up access."
        )
        if prompt_confirm("Open Snowflake console in browser?", default=True):
            import webbrowser

            webbrowser.open("https://app.snowflake.com/")
            console.print("[dim]Opened in browser. Come back here when ready.[/dim]")
        console.print()

    # Ask setup questions first, then show SQL
    choices = provider.collect_setup_choices(partial_choices)
    run_onboarding(provider, choices)
    auth_method = choices.get("auth_method", auth_method)
    track(DB_CONNECT_SETUP_COMPLETED, provider=provider_name, auth_method=auth_method)

    # Collect credentials (PAT prompt comes first if applicable)
    credentials = provider.collect_credentials(choices)
    track(DB_CONNECT_CREDENTIALS_ENTERED, provider=provider_name, auth_method=auth_method)
    review_fields = provider.get_review_fields(credentials)
    show_review_panel(review_fields)
    track(DB_CONNECT_REVIEW_SHOWN, provider=provider_name, auth_method=auth_method)

    if not prompt_confirm("Connect?", default=True):
        track(DB_CONNECT_ABORTED, provider=provider_name, auth_method=auth_method)
        raise typer.Exit(0)

    track(DB_CONNECT_SUBMITTED, provider=provider_name, auth_method=auth_method)

    # Encrypt, submit, and wait for connection
    submit_start = time.monotonic()
    with get_authenticated_client() as client:
        result = encrypt_and_submit(client, provider_name, credentials, review_fields)
        status, skipped = wait_for_connection(client, result.id)
    time_to_connect_ms = int((time.monotonic() - submit_start) * 1000)

    from datafrey_api import DatabaseStatus
    from datafrey.ui.display import print_success, print_warning

    if skipped:
        track(
            DB_CONNECT_FAILED,
            provider=provider_name,
            auth_method=auth_method,
            status="skipped",
        )
        console.print("[dim]Skipped. Check connection status: datafrey db list[/dim]")
    elif status == DatabaseStatus.connected:
        track(
            DB_CONNECT_CONNECTED,
            provider=provider_name,
            auth_method=auth_method,
            time_to_connect_ms=time_to_connect_ms,
        )
        print_success("Connected!")
        _offer_index(result.id)
    elif status == DatabaseStatus.error:
        track(
            DB_CONNECT_FAILED,
            provider=provider_name,
            auth_method=auth_method,
            status="error",
        )
        print_warning("Connection failed. Check your credentials and try again.")
        raise typer.Exit(1)
    elif status is None:
        track(
            DB_CONNECT_FAILED,
            provider=provider_name,
            auth_method=auth_method,
            status="timeout",
        )
        print_warning("Connection is taking longer than expected.")
        print_hint("Check status: datafrey db list")
        raise typer.Exit(1)
    else:
        track(
            DB_CONNECT_FAILED,
            provider=provider_name,
            auth_method=auth_method,
            status=status.value,
        )
        print_warning(f"Connection status: {status.value}")
        raise typer.Exit(1)

    from datafrey.cli.client import _run_interactive_menu

    _run_interactive_menu(source="post_connect")
