from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
import json
from typing import Any

import httpx
from openai import AsyncOpenAI

from helm.providers.base import ChatMessage, ProviderResponse, ToolCall


@dataclass(slots=True)
class OpenAICompatibleProvider:
    id: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 120

    async def complete(self, messages: list[ChatMessage], **kwargs: object) -> ProviderResponse:
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            trust_env=False,
        ) as http_client:
            client = AsyncOpenAI(
                base_url=self.base_url.rstrip("/") + "/",
                api_key=self.api_key,
                http_client=http_client,
            )
            response = await client.chat.completions.create(
                **self._request_params(messages, kwargs)
            )
            return self._parse_response(response.model_dump())

    async def stream(
        self,
        messages: list[ChatMessage],
        **kwargs: object,
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            trust_env=False,
        ) as http_client:
            client = AsyncOpenAI(
                base_url=self.base_url.rstrip("/") + "/",
                api_key=self.api_key,
                http_client=http_client,
            )
            stream = await client.chat.completions.create(
                **self._request_params(messages, kwargs),
                stream=True,
            )
            async for chunk in stream:
                for choice in chunk.choices:
                    delta = choice.delta.content
                    if delta:
                        yield delta

    def _request_params(
        self,
        messages: list[ChatMessage],
        kwargs: dict[str, object],
    ) -> dict[str, Any]:
        request_params: dict[str, Any] = {
            "model": str(kwargs.get("model") or self.model),
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            "temperature": float(kwargs.get("temperature", 0.2)),
        }
        if kwargs.get("tools") is not None:
            request_params["tools"] = kwargs["tools"]
        if kwargs.get("max_tokens") is not None:
            request_params["max_tokens"] = int(kwargs["max_tokens"])
        if kwargs.get("extra_body") is not None:
            request_params["extra_body"] = kwargs["extra_body"]
        return request_params

    def _parse_response(self, response: dict[str, Any]) -> ProviderResponse:
        choices = response.get("choices") or []
        if not choices:
            return ProviderResponse(content="", raw=response)

        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        tool_calls: list[ToolCall] = []
        for item in message.get("tool_calls") or []:
            function = item.get("function") or {}
            raw_arguments = function.get("arguments") or "{}"
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                arguments = {"raw": raw_arguments}
            tool_calls.append(
                ToolCall(
                    name=str(function.get("name") or ""),
                    arguments=arguments,
                )
            )
        return ProviderResponse(content=str(content), tool_calls=tool_calls, raw=response)
