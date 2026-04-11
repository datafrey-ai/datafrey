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
    from datafrey.ui.display import print_success

    console.print()
    console.print(
        "Schema indexing lets the AI understand your database structure for better query planning."
    )
    if prompt_confirm("Index schema now? (recommended)", default=True):
        with get_authenticated_client() as client:
            client.reindex_database(db_id)
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
    from datafrey.auth.middleware import get_authenticated_client
    from datafrey.cli.onboarding import (
        encrypt_and_submit,
        ensure_recent_auth,
        run_onboarding,
        wait_for_connection,
    )
    from datafrey.providers.base import get_provider, get_provider_choices
    from datafrey.ui.prompts import prompt_select

    import datafrey.providers  # noqa: F401 — populates provider registry

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
    provider = get_provider(provider_name)

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
    choices = provider.collect_setup_choices()
    run_onboarding(provider, choices)

    # Collect credentials (PAT prompt comes first if applicable)
    credentials = provider.collect_credentials(choices)
    review_fields = provider.get_review_fields(credentials)
    show_review_panel(review_fields)

    if not prompt_confirm("Connect?", default=True):
        raise typer.Exit(0)

    # Encrypt, submit, and wait for connection
    with get_authenticated_client() as client:
        result = encrypt_and_submit(client, provider_name, credentials, review_fields)
        status, skipped = wait_for_connection(client, result.id)

    from datafrey_api import DatabaseStatus
    from datafrey.ui.display import print_success, print_warning

    if skipped:
        console.print("[dim]Skipped. Check connection status: datafrey db list[/dim]")
    elif status == DatabaseStatus.connected:
        print_success("Connected!")
        _offer_index(result.id)
    elif status == DatabaseStatus.error:
        print_warning("Connection failed. Check your credentials and try again.")
        raise typer.Exit(1)
    elif status is None:
        print_warning("Connection is taking longer than expected.")
        print_hint("Check status: datafrey db list")
        raise typer.Exit(1)
    else:
        print_warning(f"Connection status: {status.value}")
        raise typer.Exit(1)

    from datafrey.cli.client import _run_interactive_menu

    _run_interactive_menu()
