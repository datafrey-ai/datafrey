"""index command: sync the database schema index."""

from __future__ import annotations

import typer

from datafrey.ui.console import console
from datafrey.ui.display import print_success


def index_command() -> None:
    """Sync the database schema index."""
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
