"""Telemetry: PostHog event tracking with opt-out + WorkOS identity."""

from datafrey_mcp.telemetry.client import flush, track

__all__ = ["flush", "track"]
