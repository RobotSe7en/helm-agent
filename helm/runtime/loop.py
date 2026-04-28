from __future__ import annotations

import json

from helm.context.context_builder import ContextBuilder
from helm.providers.base import ChatMessage
from helm.providers.resolver import ProviderResolver
from helm.runtime.invocation import RuntimeInvocation
from helm.runtime.result import RuntimeResult
from helm.runtime.tool_dispatcher import ToolDispatcher


class RuntimeLoop:
    """Hermes-style v0 agent loop.

    The current backbone supports provider calls and tool dispatch plumbing.
    Full multi-turn tool-call continuation can build on this same interface.
    """

    def __init__(
        self,
        context_builder: ContextBuilder,
        provider_resolver: ProviderResolver,
        tool_dispatcher: ToolDispatcher | None = None,
        max_iterations: int = 8,
    ):
        self.context_builder = context_builder
        self.provider_resolver = provider_resolver
        self.tool_dispatcher = tool_dispatcher
        self.max_iterations = max_iterations

    async def invoke(self, invocation: RuntimeInvocation) -> RuntimeResult:
        profile = self.context_builder.resolve_profile(invocation)
        active_skills = [
            skill.id for skill in self.context_builder.resolve_skills(profile, invocation)
        ]
        messages = self.context_builder.build_messages(invocation)
        provider = self.provider_resolver.resolve(profile, invocation.provider)
        allowed_toolsets = list(dict.fromkeys([*profile.default_toolsets, *invocation.toolsets]))
        provider_kwargs = {
            key: invocation.metadata[key]
            for key in ("model", "temperature", "max_tokens", "tools", "extra_body")
            if key in invocation.metadata
        }
        if (
            "tools" not in provider_kwargs
            and self.tool_dispatcher is not None
            and allowed_toolsets
        ):
            provider_kwargs["tools"] = self.tool_dispatcher.schemas_for_toolsets(
                allowed_toolsets
            )
        tool_names = [
            schema["function"]["name"]
            for schema in provider_kwargs.get("tools", [])
            if isinstance(schema, dict) and isinstance(schema.get("function"), dict)
        ]

        events: list[dict[str, object]] = [
            {
                "type": "runtime.started",
                "profile": profile.id,
                "skills": active_skills,
                "toolsets": allowed_toolsets,
                "tools": tool_names,
                "task_id": invocation.task_id,
            }
        ]
        max_iterations = (
            invocation.max_iterations
            or profile.max_iterations
            or self.max_iterations
        )
        for iteration in range(1, max_iterations + 1):
            response = await provider.complete(messages, **provider_kwargs)
            events.append(
                {
                    "type": "provider.completed",
                    "provider": provider.id,
                    "profile": profile.id,
                    "task_id": invocation.task_id,
                    "iteration": iteration,
                    "tool_call_count": len(response.tool_calls),
                }
            )

            if not response.tool_calls:
                return RuntimeResult(
                    status="completed",
                    output=response.content,
                    events=events,
                )

            if self.tool_dispatcher is None:
                return RuntimeResult(
                    status="failed",
                    output="Provider requested tool calls but no dispatcher is configured.",
                    events=events,
                    error="missing_tool_dispatcher",
                )

            tool_events: list[dict[str, object]] = []
            for tool_call in response.tool_calls:
                tool_result = await self.tool_dispatcher.dispatch(
                    tool_call,
                    allowed_toolsets=allowed_toolsets,
                )
                tool_event = {
                    "type": "tool.completed",
                    "tool": tool_call.name,
                    "arguments": tool_call.arguments,
                    "ok": tool_result.ok,
                    "content": tool_result.content,
                    "iteration": iteration,
                }
                events.append(tool_event)
                tool_events.append(tool_event)

            messages.append(
                ChatMessage(
                    role="user",
                    content=(
                        "Tool calls completed. Use these results to decide whether "
                        "to call more tools or produce the final answer:\n"
                        f"{json.dumps(tool_events, ensure_ascii=False)}"
                    ),
                )
            )

        return RuntimeResult(
            status="failed",
            output=f"Runtime exceeded max iterations: {max_iterations}",
            events=events,
            error="max_iterations_exceeded",
        )
