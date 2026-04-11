"""DatabaseProvider ABC and provider registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from questionary import Choice


class DatabaseProvider(ABC):
    """Abstract base for database providers."""

    name: str
    display_name: str

    @abstractmethod
    def collect_setup_choices(self) -> dict:
        """Prompt user for setup choices (auth method, access scope, etc.)."""
        ...

    @abstractmethod
    def get_onboarding_steps(self, choices: dict) -> list[tuple[str, str]]:
        """Return list of (title, sql) tuples for onboarding panels."""
        ...

    @abstractmethod
    def collect_credentials(self, choices: dict) -> dict[str, str]:
        """Prompt user for credentials. Returns field dict."""
        ...

    @abstractmethod
    def get_review_fields(self, credentials: dict[str, str]) -> dict[str, str]:
        """Return fields to show in review panel (no secrets)."""
        ...


def get_provider_choices() -> list[Choice]:
    """Return questionary choices for supported providers."""
    from questionary import Choice

    return [
        Choice("Snowflake", value="snowflake"),
    ]


PROVIDERS: dict[str, type[DatabaseProvider]] = {}


def register_provider(cls: type[DatabaseProvider]) -> type[DatabaseProvider]:
    PROVIDERS[cls.name] = cls
    return cls


def get_provider(name: str) -> DatabaseProvider:
    return PROVIDERS[name]()
