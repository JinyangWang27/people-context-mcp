"""SQLite-backed replayable changelog."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from datetime import datetime

from people_context.adapters.sqlite.unit_of_work import SqliteUnitOfWork
from people_context.ports.changelog import ChangelogEntry


class SqliteChangelog:
    """Persist full replay operations in HLC order."""

    def __init__(self, conn: sqlite3.Connection, failure_hook: Callable[[str], None] | None = None) -> None:
        self._conn = conn
        self._failure_hook = failure_hook

    def append(self, entry: ChangelogEntry) -> None:
        with SqliteUnitOfWork(self._conn):
            if self._failure_hook is not None:
                self._failure_hook("before_append")
            self._conn.execute(
                """INSERT INTO changelog (
                       op_id, device_id, hlc_physical_ms, hlc_logical, transaction_id,
                       entity_type, entity_id, op_kind, payload_json, changed_fields_json,
                       actor_json, schema_version, inserted_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.op_id,
                    entry.device_id,
                    entry.hlc_physical_ms,
                    entry.hlc_logical,
                    entry.transaction_id,
                    entry.entity_type,
                    entry.entity_id,
                    entry.op_kind,
                    json.dumps(entry.payload, ensure_ascii=False, sort_keys=True),
                    json.dumps(entry.changed_fields, ensure_ascii=False),
                    json.dumps(entry.actor, ensure_ascii=False, sort_keys=True),
                    entry.schema_version,
                    entry.inserted_at.isoformat(),
                ),
            )

    def list_entries(self, limit: int = 100, entity_id: str | None = None) -> list[ChangelogEntry]:
        clauses = "WHERE entity_id = ?" if entity_id is not None else ""
        params: tuple[object, ...] = (entity_id, limit) if entity_id is not None else (limit,)
        rows = self._conn.execute(
            f"""SELECT * FROM changelog {clauses}
                ORDER BY hlc_physical_ms DESC, hlc_logical DESC, device_id DESC, op_id DESC LIMIT ?""",
            params,
        ).fetchall()
        return [self._hydrate(row) for row in rows]

    @staticmethod
    def _hydrate(row: sqlite3.Row) -> ChangelogEntry:
        return ChangelogEntry(
            op_id=row["op_id"],
            device_id=row["device_id"],
            hlc_physical_ms=row["hlc_physical_ms"],
            hlc_logical=row["hlc_logical"],
            transaction_id=row["transaction_id"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            op_kind=row["op_kind"],
            payload=json.loads(row["payload_json"]),
            changed_fields=json.loads(row["changed_fields_json"]),
            actor=json.loads(row["actor_json"]),
            schema_version=row["schema_version"],
            inserted_at=datetime.fromisoformat(row["inserted_at"]),
        )
