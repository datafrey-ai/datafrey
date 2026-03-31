"""Two-console pattern: stdout for data, stderr for errors."""

from rich.console import Console

console = Console()  # stdout — data, tables, panels
err_console = Console(stderr=True)  # stderr — errors, spinners, progress
