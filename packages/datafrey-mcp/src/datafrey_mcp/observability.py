"""Sentry initialisation for the MCP server.

Reads `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_RELEASE` from the environment.
No-op when `SENTRY_DSN` is unset so local runs and users self-hosting the OSS
image don't need a DSN configured.
"""

from __future__ import annotations

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

_initialized = False


def init_sentry() -> None:
    global _initialized
    if _initialized:
        return

    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "dev"),
        release=os.environ.get("SENTRY_RELEASE"),
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
        integrations=[
            AsyncioIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
    )
    _initialized = True
