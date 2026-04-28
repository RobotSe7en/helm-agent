from __future__ import annotations

from collections.abc import AsyncIterator

from helm.providers.base import ChatMessage, ProviderResponse


class EchoProvider:
    id = "echo"

    async def complete(self, messages: list[ChatMessage], **kwargs: object) -> ProviderResponse:
        user_messages = [message.content for message in messages if message.role == "user"]
        last = user_messages[-1] if user_messages else messages[-1].content
        return ProviderResponse(content=f"[echo] Completed invocation for: {last}")

    async def stream(self, messages: list[ChatMessage], **kwargs: object) -> AsyncIterator[str]:
        response = await self.complete(messages, **kwargs)
        yield response.content
