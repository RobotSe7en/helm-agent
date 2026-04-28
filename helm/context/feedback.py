from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class Feedback:
    run_id: str
    content: str
    rating: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
