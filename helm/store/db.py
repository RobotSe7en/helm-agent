from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from helm.context.events import Event


class SQLiteStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.migrate()

    def migrate(self) -> None:
        self.connection.execute(
            """
            create table if not exists events (
              id text primary key,
              run_id text not null,
              task_id text,
              type text not null,
              payload text not null,
              created_at text not null
            )
            """
        )
        self.connection.commit()

    def append_event(self, event: Event) -> None:
        self.connection.execute(
            """
            insert into events (id, run_id, task_id, type, payload, created_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.run_id,
                event.task_id,
                event.type,
                json.dumps(event.payload),
                event.created_at.isoformat(),
            ),
        )
        self.connection.commit()

    def list_events(self, run_id: str) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "select * from events where run_id = ? order by created_at asc",
            (run_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "run_id": row["run_id"],
                "task_id": row["task_id"],
                "type": row["type"],
                "payload": json.loads(row["payload"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
