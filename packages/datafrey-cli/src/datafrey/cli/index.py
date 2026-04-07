"""index subgroup: sync and status."""

from __future__ import annotations

from typing import Annotated

import typer

from datafrey.ui.console import console
from datafrey.ui.display import print_hint, print_json_success, print_success

index_app = typer.Typer(no_args_is_help=True)


def _get_database_id() -> str:
    from datafrey.auth.middleware import get_authenticated_client

    with get_authenticated_client() as client:
        databases = client.list_databases()
    if not databases:
        console.print("No databases connected. Run 'datafrey db connect' to add one.")
        raise typer.Exit(0)
    return databases[0].id


@index_app.command("sync")
def index_sync() -> None:
    """Trigger a re-index of the connected database."""
    from datafrey.auth.middleware import get_authenticated_client

    with get_authenticated_client() as client:
        databases = client.list_databases()
        if not databases:
            console.print(
                "No databases connected. Run 'datafrey db connect' to add one."
            )
            raise typer.Exit(0)
        client.reindex_database(databases[0].id)

    print_success("Indexing started.")
    print_hint("Run 'datafrey index status' to check progress.")


@index_app.command("status")
def index_status(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON.")
    ] = False,
) -> None:
    """Show the index status for the connected database."""
    from datafrey.auth.middleware import get_authenticated_client
    from datafrey.ui.display import show_index_status

    with get_authenticated_client() as client:
        databases = client.list_databases()
        if not databases:
            console.print(
                "No databases connected. Run 'datafrey db connect' to add one."
            )
            raise typer.Exit(0)
        status = client.get_index_status(databases[0].id)

    if json_output:
        print_json_success(status.model_dump(mode="json"))
        return

    show_index_status(status)
