"""client subgroup: configure AI clients."""

from __future__ import annotations

import json
import subprocess
import webbrowser

import typer

from datafrey.ui.console import console
from datafrey.ui.display import (
    print_docs_link,
    print_hint,
    print_success,
    show_mcp_config,
)

MCP_URL = "https://mcp.datafrey.ai/mcp"

DATAFREY_MCP_CONFIG = {"url": MCP_URL}

CLIENT_CHOICES = ["Claude Code", "Cursor", "MCP (Custom)"]
# Claude Desktop is not yet tested/supported
# CLIENT_CHOICES = ["Claude Code", "Claude Desktop", "Cursor", "MCP (Custom)"]

client_app = typer.Typer(
    name="client",
    help="Configure an AI client to use Datafrey.",
    invoke_without_command=True,
    no_args_is_help=False,
)


def _setup_claude_code() -> None:
    """Configure Claude Code by installing the Datafrey plugin."""
    from datafrey.ui.display import print_error

    commands = [
        ["claude", "plugin", "marketplace", "add", "datafrey-ai/datafrey"],
        ["claude", "plugin", "install", "datafrey@datafrey"],
    ]

    for cmd in commands:
        console.print(f"[dim]Running: {' '.join(cmd)}[/]\n")
        try:
            result = subprocess.run(cmd, check=False)
        except FileNotFoundError:
            print_error(
                "'claude' command not found.",
                "Install Claude Code first: https://docs.anthropic.com/en/docs/claude-code",
            )
            return
        if result.returncode != 0:
            print_error(
                "Command failed.",
                "Make sure Claude Code CLI is installed: https://docs.anthropic.com/en/docs/claude-code",
            )
            return

    print_success("Datafrey plugin installed in Claude Code.")
    console.print()
    console.print("Next steps:")
    console.print("  1. Run [bold]claude[/] to start Claude Code")
    console.print("  2. Inside Claude Code, run [bold]/mcp enable datafrey[/] to enable the MCP server")
    console.print("  3. Use [bold]/db[/] to query your database")


def _setup_cursor() -> None:
    import base64

    config = base64.b64encode(
        json.dumps(DATAFREY_MCP_CONFIG, separators=(",", ":")).encode()
    ).decode()
    url = f"cursor://anysphere.cursor-deeplink/mcp/install?name=datafrey&config={config}"
    try:
        webbrowser.open(url)
        print_success("Opening Cursor install dialog...")
    except Exception:
        console.print("[dim]Could not open automatically. Click the link below:[/]")
        console.print(f"\n  [blue][link={url}]{url}[/link][/blue]\n")
    console.print()
    console.print("Next steps:")
    console.print("  1. Click [bold]Install[/] in the Cursor dialog")
    console.print("  2. Authenticate when Cursor connects to the MCP server")
    console.print("  3. Ask Cursor about your database")
    console.print()
    print_hint(
        "To also get the [bold]/db[/] skill: run [bold]datafrey client claude[/] — "
        "Cursor will suggest installing the plugin automatically."
    )


def _setup_custom() -> None:
    """Display JSON config for manual setup."""
    console.print("\nAdd this to your MCP client config:\n")
    config_json = json.dumps(
        {"mcpServers": {"datafrey": DATAFREY_MCP_CONFIG}}, indent=2
    )
    show_mcp_config(config_json)

    from datafrey.ui.clipboard import copy_to_clipboard

    if copy_to_clipboard(config_json):
        console.print("[dim]Copied to clipboard.[/]")


def _print_footer() -> None:
    console.print()
    console.print("Authentication handled automatically when MCP client connects.")
    print_docs_link("mcp")


def _run_interactive_menu() -> None:
    """Show the interactive client selection menu."""
    from datafrey.ui.prompts import prompt_select

    choice = prompt_select("Select your AI client:", CLIENT_CHOICES)

    if choice == "Claude Code":
        _setup_claude_code()
    # elif choice == "Claude Desktop":
    #     _setup_config_client("claude_desktop", "Claude Desktop")
    elif choice == "Cursor":
        _setup_cursor()
    elif choice == "MCP (Custom)":
        _setup_custom()

    _print_footer()


@client_app.callback()
def client_callback(ctx: typer.Context) -> None:
    """Configure an AI client to use Datafrey."""
    if ctx.invoked_subcommand is None:
        _run_interactive_menu()


@client_app.command("claude")
def client_claude() -> None:
    """Configure Claude Code."""
    _setup_claude_code()
    _print_footer()


@client_app.command("cursor")
def client_cursor() -> None:
    """Configure Cursor."""
    _setup_cursor()
    _print_footer()


@client_app.command("mcp")
def client_mcp() -> None:
    """Print MCP config block for any MCP-compatible client."""
    _setup_custom()
    _print_footer()
