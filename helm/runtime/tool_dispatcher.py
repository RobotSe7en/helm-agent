from __future__ import annotations

from helm.providers.base import ToolCall
from helm.tools.base import ToolResult
from helm.tools.registry import ToolRegistry
from helm.tools.toolsets import expand_toolsets


class ToolDispatcher:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def dispatch(
        self,
        tool_call: ToolCall,
        allowed_toolsets: list[str],
    ) -> ToolResult:
        allowed_tools = set(expand_toolsets(allowed_toolsets))
        try:
            internal_name = self.registry.get(tool_call.name).name
        except KeyError:
            return ToolResult(
                ok=False,
                content=f"Unknown tool requested by model: {tool_call.name}",
            )
        if internal_name not in allowed_tools:
            return ToolResult(
                ok=False,
                content=f"Tool is not allowed for this invocation: {tool_call.name}",
            )
        tool = self.registry.get(internal_name)
        return await tool.run(**tool_call.arguments)

    def schemas_for_toolsets(self, allowed_toolsets: list[str]) -> list[dict[str, object]]:
        return self.registry.schemas_for(expand_toolsets(allowed_toolsets))
