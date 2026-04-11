"""Rich display helpers: tables, panels, status outputs."""

from __future__ import annotations

from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from datafrey.ui.console import console, err_console

# ── Docs links ──

_DOCS_BASE = "https://docs.datafrey.ai"

DOCS: dict[str, str] = {
    "getting-started": _DOCS_BASE,
    "login": _DOCS_BASE,
    "db-connect": _DOCS_BASE,
    "encryption": _DOCS_BASE,
    "mcp": _DOCS_BASE,
    "troubleshooting": _DOCS_BASE,
    "db-list": _DOCS_BASE,
}


def _docs_ref(key: str) -> str:
    """Return Rich markup for an inline docs hyperlink."""
    url = DOCS[key]
    short = url.replace("https://", "")
    return f"[blue][link={url}]{short}[/link][/blue]"


def print_docs_link(key: str) -> None:
    """Print a contextual docs link (for non-panel steps)."""
    console.print(f"  {_docs_ref(key)}")


def print_error(message: str, hint: str = "") -> None:
    """Print formatted error to stderr."""
    err_console.print(f"[bold red]Error:[/] {message}")
    if hint:
        for line in hint.split("\n"):
            err_console.print(f"[dim]→ {line}[/]")


def print_success(message: str) -> None:
    console.print(f"[green]✓[/] {message}")


def print_hint(message: str) -> None:
    console.print(f"[dim]Tip: {message}[/]")


def print_warning(message: str) -> None:
    err_console.print(f"[bold yellow]⚠[/] {message}")


def print_json_error(error: str, message: str, hint: str = "") -> None:
    """Print JSON-formatted error to stderr."""
    import json

    err_console.print(
        json.dumps(
            {"status": "error", "error": error, "message": message, "hint": hint}
        )
    )


def print_json_success(data: dict) -> None:
    """Print JSON-formatted success to stdout."""
    import json

    console.print(json.dumps({"status": "ok", "data": data}))


def show_device_code_panel(
    user_code: str, verification_uri: str, *, copied: bool = False
) -> None:
    copy_line = (
        "  [green]✓ Code copied to clipboard — paste it in the browser.[/]"
        if copied
        else "  [dim]Copy the code above and enter it in the browser.[/]"
    )
    panel = Panel(
        f"\n  Your confirmation code:\n\n"
        f"           [bold]{user_code}[/]\n\n"
        f"  Enter this code at:\n"
        f"  {verification_uri}\n\n"
        f"{copy_line}\n",
        subtitle=_docs_ref("login"),
        expand=False,
    )
    console.print(panel)


def show_welcome_panel(version: str) -> None:
    panel = Panel(
        f"  Welcome to Datafrey CLI  v{version}\n  datafrey.ai",
        subtitle=_docs_ref("getting-started"),
        expand=False,
    )
    console.print(panel)
    console.print("Connect your database once, query it from any AI.\n")


def show_databases_table(databases: list) -> None:
    """Render databases as a Rich table."""
    table = Table()
    table.add_column("ID", style="dim")
    table.add_column("Provider")
    table.add_column("Name")
    table.add_column("Host")
    table.add_column("Status")
    table.add_column("Created")
    for db in databases:
        status_style = (
            "green" if db.status.value == "connected"
            else "yellow" if db.status.value == "loading"
            else "red"
        )
        table.add_row(
            db.id,
            db.provider.value,
            db.name,
            db.host,
            f"[{status_style}]{db.status.value}[/]",
            db.created_at.strftime("%Y-%m-%d"),
        )
    console.print(table)


def show_status(email: str, name: str, db=None, index_status=None) -> None:
    console.print(f"User:       {email} ({name})")
    if db is None:
        console.print("Database:   [dim]none[/]")
        print_hint("Run 'datafrey db connect' to add one.")
        return
    db_connected = db.status.value == "connected"
    status_label = "" if db_connected else f" [{db.status.value}]"
    console.print(f"Database:   {db.host}{status_label}")
    if not db_connected:
        console.print("Index:      [dim]not available (database not connected)[/]")
        return
    if index_status is None or index_status.indexed_at is None:
        console.print("Index:      [dim]not built[/]")
        print_hint("Run 'datafrey index' to build the index.")
        return
    console.print(f"Indexed:    {index_status.indexed_at.strftime('%Y-%m-%d %H:%M UTC')}")
    console.print(f"Tables:     {index_status.table_count}")
    console.print(f"Columns:    {index_status.column_count}")


def show_review_panel(fields: dict[str, str]) -> None:
    """Show a review panel for db connect."""
    rows = "\n".join(f"  {k:<14}{v}" for k, v in fields.items())
    panel = Panel(
        rows, title="Review Connection", subtitle=_docs_ref("db-connect"), expand=False
    )
    console.print(panel)


def show_onboarding_panel(title: str, sql: str) -> None:
    syntax = Syntax(sql, "sql", theme="monokai", padding=1)
    nav = (
        "[bold cyan]\\[C] COPY[/bold cyan]"
        "  ·  "
        "[bold green]\\[Enter] CONTINUE[/bold green]"
        "  ·  "
        "[dim]\\[^C] Cancel[/dim]"
    )
    panel = Panel(
        syntax,
        title=title,
        subtitle=nav,
        expand=False,
    )
    console.print(panel)


def show_connection_result(
    db_id: str, provider: str, name: str, host: str, status: str
) -> None:
    console.print()
    print_success(f"Database connected: {name}")
    console.print(f"  ID:       {db_id}")
    console.print(f"  Provider: {provider}")
    console.print(f"  Host:     {host}")
    console.print(f"  Status:   {status}")
    print_docs_link("mcp")


def show_mcp_config(config_json: str) -> None:
    syntax = Syntax(config_json, "json", theme="monokai", padding=1)
    console.print(syntax)


def show_index_status(index_status) -> None:
    """Display index status in a readable format."""
    if index_status.indexed_at is None:
        console.print("Index:      [dim]not built[/]")
        print_hint("Run 'datafrey index' to build the index.")
        return

    console.print(f"Indexed:    {index_status.indexed_at.strftime('%Y-%m-%d %H:%M UTC')}")
    console.print(f"Tables:     {index_status.table_count}")
    console.print(f"Columns:    {index_status.column_count}")


def show_security_warning(expected: str, got: str) -> None:
    """Show a warning panel for server key fingerprint mismatch."""
    panel = Panel(
        f"[bold red]Server key fingerprint mismatch![/]\n\n"
        f"  Expected: {expected}\n"
        f"  Got:      {got}\n\n"
        "[bold]This could indicate a man-in-the-middle attack.[/]\n"
        "[bold]Do NOT proceed. Contact support@datafrey.ai.[/]",
        title="Security Warning",
        border_style="red",
        expand=False,
    )
    err_console.print(panel)
