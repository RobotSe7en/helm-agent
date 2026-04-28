from __future__ import annotations

from dataclasses import dataclass

from helm.runtime.delegation import DelegationManager
from helm.tools.base import ToolResult


@dataclass(slots=True)
class DelegateTaskTool:
    manager: DelegationManager
    name: str = "delegate_task"
    description: str = "Spawn an isolated child runtime invocation."
    parameters: dict[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.parameters = {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "context": {"type": "string"},
                "profile": {"type": "string"},
                "skills": {"type": "array", "items": {"type": "string"}},
                "toolsets": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["goal"],
        }

    async def run(self, **kwargs: object) -> ToolResult:
        result = await self.manager.delegate(
            goal=str(kwargs["goal"]),
            context=str(kwargs.get("context") or ""),
            profile=kwargs.get("profile"),
            skills=list(kwargs.get("skills") or []),
            toolsets=list(kwargs.get("toolsets") or []),
        )
        return ToolResult(ok=True, content=result.output, metadata={"status": result.status})
