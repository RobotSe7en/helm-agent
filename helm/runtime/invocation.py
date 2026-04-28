from __future__ import annotations

from dataclasses import dataclass, field

from helm.profiles.schema import AgentProfile


@dataclass(slots=True)
class RuntimeInvocation:
    run_id: str
    goal: str
    instructions: str
    profile: str = "default"
    task_id: str | None = None
    skills: list[str] = field(default_factory=list)
    toolsets: list[str] = field(default_factory=list)
    provider: str | None = None
    max_iterations: int | None = None
    depth: int = 0
    metadata: dict[str, object] = field(default_factory=dict)
    profile_obj: AgentProfile | None = None
