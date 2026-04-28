from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


@dataclass(slots=True)
class ToolCall:
    name: str
    arguments: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: object | None = None


class Provider(Protocol):
    id: str

    async def complete(self, messages: list[ChatMessage], **kwargs: object) -> ProviderResponse:
        ...
