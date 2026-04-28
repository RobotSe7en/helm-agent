from __future__ import annotations

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
        client = AsyncOpenAI(
            base_url=self.base_url.rstrip("/") + "/",
            api_key=self.api_key,
            http_client=httpx.AsyncClient(
                timeout=self.timeout_seconds,
                trust_env=False,
            ),
        )
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

        response = await client.chat.completions.create(**request_params)
        return self._parse_response(response.model_dump())

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
