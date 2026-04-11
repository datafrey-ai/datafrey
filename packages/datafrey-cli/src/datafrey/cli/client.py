"""client subgroup: configure AI clients."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import typer

from datafrey.ui.console import console
from datafrey.ui.display import (
    print_docs_link,
    print_hint,
    print_success,
    show_mcp_config,
)

MCP_URL = "https://mcp.datafrey.ai/mcp"

# Client config file paths per platform
_CLIENT_CONFIGS: dict[str, dict[str, Path]] = {
    # "claude_desktop": {
    #     "darwin": Path.home()
    #     / "Library"
    #     / "Application Support"
    #     / "Claude"
    #     / "claude_desktop_config.json",
    #     "linux": Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
    #     "win32": Path(str(Path.home()).replace("/", "\\"))
    #     / "AppData"
    #     / "Roaming"
    #     / "Claude"
    #     / "claude_desktop_config.json",
    # },
    "cursor": {
        "all": Path.home() / ".cursor" / "mcp.json",
    },
}

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


def _get_config_path(client: str) -> Path | None:
    """Get the config file path for a client on this platform."""
    paths = _CLIENT_CONFIGS.get(client, {})
    return paths.get(sys.platform) or paths.get("all")


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
    console.print("  2. Run [bold]claude mcp enable datafrey[/] to enable the MCP server")
    console.print("  3. Use [bold]/db[/] to query your database")


def _setup_config_client(client_key: str, label: str) -> None:
    """Patch a JSON config file for Cursor or similar clients."""
    path = _get_config_path(client_key)
    if path is None:
        from datafrey.ui.display import print_error

        print_error(f"Could not determine config path for {label} on this platform.")
        return

    _patch_config(path)
    print_success(f"Updated {label} config at {path}")
    print_hint(f"Restart {label} to apply.")


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
        _setup_config_client("cursor", "Cursor")
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
    _setup_config_client("cursor", "Cursor")
    _print_footer()


@client_app.command("mcp")
def client_mcp() -> None:
    """Print MCP config block for any MCP-compatible client."""
    _setup_custom()
    _print_footer()


def _patch_config(config_path: Path) -> None:
    """Read existing config, merge datafrey MCP server, write back."""
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            existing = {}
    else:
        existing = {}

    if "mcpServers" not in existing:
        existing["mcpServers"] = {}
    existing["mcpServers"]["datafrey"] = DATAFREY_MCP_CONFIG

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(existing, indent=2) + "\n")
