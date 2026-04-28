from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(slots=True)
class Event:
    run_id: str
    type: str
    payload: dict[str, object]
    task_id: str | None = None
    id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
