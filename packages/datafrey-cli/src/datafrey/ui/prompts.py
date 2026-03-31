"""Reusable prompt helpers wrapping questionary."""

from __future__ import annotations

import re


def prompt_text(
    message: str,
    default: str = "",
    validate_pattern: str | None = None,
    optional: bool = False,
) -> str:
    import questionary

    def validator(text: str) -> bool | str:
        if not optional and not text.strip():
            return "This field is required."
        if validate_pattern and text.strip() and not re.match(validate_pattern, text):
            return f"Must match pattern: {validate_pattern}"
        return True

    display_message = f"{message} (optional, Enter to skip)" if optional else message
    result = questionary.text(
        display_message, default=default, validate=validator
    ).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def prompt_password(message: str, optional: bool = False) -> str:
    import questionary

    def validator(text: str) -> bool | str:
        if not optional and not text:
            return "This field is required."
        return True

    result = questionary.password(message, validate=validator).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def prompt_confirm(message: str, default: bool = True) -> bool:
    import questionary

    result = questionary.confirm(message, default=default).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def prompt_select(message: str, choices: list) -> str:
    import questionary

    result = questionary.select(message, choices=choices).ask()
    if result is None:
        raise KeyboardInterrupt
    return result
