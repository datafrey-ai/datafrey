"""In-memory state for the mock server. Resets on restart."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from datafrey_api import DatabaseRecord, Provider, DatabaseStatus


def _seed_databases() -> dict[str, DatabaseRecord]:
    records = [
        DatabaseRecord(
            id="db_sf_abc123",
            provider=Provider.snowflake,
            name="Production Analytics",
            host="abc12345.us-east-1.snowflakecomputing.com",
            status=DatabaseStatus.connected,
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        ),
        DatabaseRecord(
            id="db_sf_def456",
            provider=Provider.snowflake,
            name="Staging Warehouse",
            host="def45678.us-west-2.snowflakecomputing.com",
            status=DatabaseStatus.connected,
            created_at=datetime(2024, 2, 20, 14, 45, 0, tzinfo=timezone.utc),
        ),
    ]
    return {r.id: r for r in records}


class MockState:
    """Mutable in-memory store for databases, keyed by user sub."""

    CONNECT_DELAY = 5.0  # seconds until loading -> connected

    def __init__(self, seed: str = "default") -> None:
        # user_sub -> {db_id -> DatabaseRecord}
        self._databases: dict[str, dict[str, DatabaseRecord]] = {}
        self._pending: dict[str, float] = {}  # db_id -> monotonic creation time
        self._seed = seed

    def databases_for(self, user_sub: str) -> dict[str, DatabaseRecord]:
        if user_sub not in self._databases:
            self._databases[user_sub] = (
                _seed_databases() if self._seed == "default" else {}
            )
        return self._databases[user_sub]

    def mark_pending(self, db_id: str) -> None:
        """Record a newly created database that starts in 'loading' status."""
        self._pending[db_id] = time.monotonic()

    def resolve_pending(self, user_sub: str) -> None:
        """Transition pending databases to 'connected' once delay has elapsed."""
        now = time.monotonic()
        dbs = self._databases.get(user_sub, {})
        for db_id in list(self._pending):
            if db_id in dbs and now - self._pending[db_id] >= self.CONNECT_DELAY:
                old = dbs[db_id]
                dbs[db_id] = DatabaseRecord(
                    id=old.id,
                    provider=old.provider,
                    name=old.name,
                    host=old.host,
                    status=DatabaseStatus.connected,
                    created_at=old.created_at,
                )
                del self._pending[db_id]

    def reset(self) -> None:
        self._databases.clear()
        self._pending.clear()
