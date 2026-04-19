"""client subgroup: configure AI clients."""

from __future__ import annotations

import json
import subprocess
import webbrowser

import typer

from datafrey.ui.console import console
from datafrey.ui.display import (
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


def _setup_claude_code() -> str | None:
    """Configure Claude Code by installing the Datafrey plugin.

    Returns ``None`` on success or a short failure-reason string.
    """
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
            return "claude_cli_not_installed"
        if result.returncode != 0:
            print_error(
                "Command failed.",
                "Make sure Claude Code CLI is installed: https://docs.anthropic.com/en/docs/claude-code",
            )
            return "subprocess_failed"

    print_success("Datafrey plugin installed in Claude Code.")
    console.print()
    console.print("Next steps:")
    console.print("  1. Run [bold]claude[/] to start Claude Code")
    console.print("  2. Inside Claude Code, run [bold]/mcp enable plugin:datafrey:datafrey[/] to enable the MCP server")
    console.print("  3. Use [bold]/db[/] to query your database")
    return None


def _setup_cursor() -> str | None:
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
    return None


def _setup_custom() -> str | None:
    """Display JSON config for manual setup."""
    console.print("\nAdd this to your MCP client config:\n")
    config_json = json.dumps(
        {"mcpServers": {"datafrey": DATAFREY_MCP_CONFIG}}, indent=2
    )
    show_mcp_config(config_json)

    from datafrey.ui.clipboard import copy_to_clipboard

    if copy_to_clipboard(config_json):
        console.print("[dim]Copied to clipboard.[/]")
    return None


def _print_footer() -> None:
    console.print()
    console.print("Authentication handled automatically when MCP client connects.")


_CHOICE_TO_KEY = {
    "Claude Code": "claude_code",
    "Cursor": "cursor",
    "MCP (Custom)": "mcp_custom",
}

_KEY_TO_SETUP = {
    "claude_code": _setup_claude_code,
    "cursor": _setup_cursor,
    "mcp_custom": _setup_custom,
}


def _run_client_setup(client_key: str, source: str) -> None:
    """Track selection + run setup + track outcome. Source = where user came from."""
    from datafrey.telemetry import track
    from datafrey.telemetry.events import (
        CLIENT_SELECTED,
        CLIENT_SETUP_COMPLETED,
        CLIENT_SETUP_FAILED,
    )

    track(CLIENT_SELECTED, client=client_key, source=source)
    setup_fn = _KEY_TO_SETUP.get(client_key)
    failure_reason = setup_fn() if setup_fn else "unknown_client"
    if failure_reason is None:
        track(CLIENT_SETUP_COMPLETED, client=client_key, source=source)
    else:
        track(
            CLIENT_SETUP_FAILED,
            client=client_key,
            source=source,
            reason=failure_reason,
        )
    _print_footer()


def _run_interactive_menu(source: str) -> None:
    """Show the interactive client selection menu."""
    from datafrey.telemetry import track
    from datafrey.telemetry.events import CLIENT_MENU_SHOWN
    from datafrey.ui.prompts import prompt_select

    track(CLIENT_MENU_SHOWN, source=source)
    choice = prompt_select("Select your AI client:", CLIENT_CHOICES)
    client_key = _CHOICE_TO_KEY.get(choice, "unknown")
    _run_client_setup(client_key, source=source)


@client_app.callback()
def client_callback(ctx: typer.Context) -> None:
    """Configure an AI client to use Datafrey."""
    if ctx.invoked_subcommand is None:
        _run_interactive_menu(source="client_command")


@client_app.command("claude")
def client_claude() -> None:
    """Configure Claude Code."""
    _run_client_setup("claude_code", source="direct_subcommand")


@client_app.command("cursor")
def client_cursor() -> None:
    """Configure Cursor."""
    _run_client_setup("cursor", source="direct_subcommand")


@client_app.command("mcp")
def client_mcp() -> None:
    """Print MCP config block for any MCP-compatible client."""
    _run_client_setup("mcp_custom", source="direct_subcommand")
