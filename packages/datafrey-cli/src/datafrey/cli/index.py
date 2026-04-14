"""index command group: sync or drop the database schema index."""

from __future__ import annotations

from typing import Annotated

import typer

from datafrey.ui.console import console
from datafrey.ui.display import print_success

index_app = typer.Typer(
    name="index",
    help="Manage the database schema index.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@index_app.callback()
def index_callback(ctx: typer.Context) -> None:
    """Sync the database schema index."""
    if ctx.invoked_subcommand is None:
        _do_reindex()


def _do_reindex() -> None:
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
    from datafrey.ui.display import print_hint
    print_hint("Run 'datafrey status' to check progress.")


@index_app.command("drop")
def index_drop(
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation.")
    ] = False,
) -> None:
    """Drop the schema index (hard reset)."""
    from datafrey.auth.middleware import get_authenticated_client
    from datafrey.ui.prompts import prompt_confirm

    with get_authenticated_client() as client:
        databases = client.list_databases()
        if not databases:
            console.print("No databases connected.")
            raise typer.Exit(0)

        if not yes:
            if not prompt_confirm("Drop the schema index?", default=False):
                raise typer.Exit(0)

        client.drop_index(databases[0].id)

    print_success("Index dropped.")
