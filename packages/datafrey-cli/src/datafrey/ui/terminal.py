"""Low-level terminal helpers (raw-mode key reading)."""

from __future__ import annotations

import sys
import termios
import tty

from datafrey.ui.clipboard import copy_to_clipboard as _copy_to_clipboard
from datafrey.ui.console import console


def onboarding_prompt(sql: str) -> None:
    """Wait for Enter/→ (continue) or C (copy). Ctrl+C raises KeyboardInterrupt."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in ("\r", "\n"):
                return
            if ch == "\x03":  # Ctrl+C
                raise KeyboardInterrupt
            if ch == "\x1b":  # Escape sequence (arrow keys)
                seq = sys.stdin.read(2)
                if seq == "[C":  # Right arrow → continue
                    return
                continue
            if ch.lower() == "c":
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                copied = _copy_to_clipboard(sql)
                console.print(
                    "  [dim]Copied to clipboard.[/]"
                    if copied
                    else "  [dim]Copy failed.[/]"
                )
                tty.setraw(fd)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
