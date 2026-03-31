"""Cross-platform clipboard copy."""

from __future__ import annotations

import platform
import subprocess


def copy_to_clipboard(text: str) -> bool:
    """Try to copy text to system clipboard. Returns True on success."""
    try:
        system = platform.system()
        if system == "Darwin":
            cmd = ["pbcopy"]
        elif system == "Linux":
            cmd = ["xclip", "-selection", "clipboard"]
        elif system == "Windows":
            cmd = ["clip"]
        else:
            return False
        subprocess.run(
            cmd, input=text.encode(), check=True, timeout=3, capture_output=True
        )
        return True
    except Exception:
        return False
