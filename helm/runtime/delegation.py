from __future__ import annotations

from dataclasses import dataclass

from helm.config.settings import Settings
from helm.profiles.adhoc import create_adhoc_profile
from helm.runtime.invocation import RuntimeInvocation
from helm.runtime.result import RuntimeResult


@dataclass(slots=True)
class DelegationManager:
    runtime: "RuntimeLoop"
    settings: Settings
    parent_run_id: str
    parent_depth: int = 0

    async def delegate(
        self,
        goal: str,
        context: str,
        profile: object | None = None,
        skills: list[str] | None = None,
        toolsets: list[str] | None = None,
    ) -> RuntimeResult:
        if self.parent_depth >= self.settings.max_delegation_depth:
            return RuntimeResult(
                status="failed",
                output="Delegation depth limit reached.",
                error="delegation_depth_limit",
            )
        if profile is None:
            profile_obj = create_adhoc_profile(goal, toolsets)
            profile_id = "adhoc"
        else:
            profile_obj = None
            profile_id = str(profile)

        return await self.runtime.invoke(
            RuntimeInvocation(
                run_id=self.parent_run_id,
                goal=goal,
                instructions=context,
                profile=profile_id,
                profile_obj=profile_obj,
                skills=skills or [],
                toolsets=toolsets or [],
                depth=self.parent_depth + 1,
            )
        )
