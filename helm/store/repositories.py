from __future__ import annotations

from helm.context.events import Event
from helm.store.db import SQLiteStore


class EventRepository:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def append(self, event: Event) -> None:
        self.store.append_event(event)

    def list_for_run(self, run_id: str) -> list[dict[str, object]]:
        return self.store.list_events(run_id)
