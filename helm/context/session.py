from __future__ import annotations

from dataclasses import dataclass, field

from helm.providers.base import ChatMessage


@dataclass(slots=True)
class SessionContext:
    run_id: str
    messages: list[ChatMessage] = field(default_factory=list)
