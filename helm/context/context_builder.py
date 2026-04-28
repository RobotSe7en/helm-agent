from __future__ import annotations

from helm.context.prompt_builder import PromptBuilder
from helm.providers.base import ChatMessage
from helm.profiles.registry import ProfileRegistry
from helm.profiles.schema import AgentProfile
from helm.runtime.invocation import RuntimeInvocation
from helm.skills.registry import SkillRegistry
from helm.skills.schema import Skill


class ContextBuilder:
    def __init__(
        self,
        profile_registry: ProfileRegistry,
        skill_registry: SkillRegistry,
        prompt_builder: PromptBuilder | None = None,
    ):
        self.profile_registry = profile_registry
        self.skill_registry = skill_registry
        self.prompt_builder = prompt_builder or PromptBuilder()

    def resolve_profile(self, invocation: RuntimeInvocation) -> AgentProfile:
        if invocation.profile_obj is not None:
            return invocation.profile_obj
        return self.profile_registry.get(invocation.profile)

    def resolve_skills(self, profile: AgentProfile, invocation: RuntimeInvocation) -> list[Skill]:
        skill_ids = list(dict.fromkeys([*profile.skills, *invocation.skills]))
        return [self.skill_registry.get(skill_id) for skill_id in skill_ids]

    def build_messages(self, invocation: RuntimeInvocation) -> list[ChatMessage]:
        profile = self.resolve_profile(invocation)
        skills = self.resolve_skills(profile, invocation)
        system_prompt = self.prompt_builder.build_system_prompt(profile, skills)
        task_context = self._build_user_context(invocation)
        return [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=task_context),
        ]

    def _build_user_context(self, invocation: RuntimeInvocation) -> str:
        parts = ["# User Request", invocation.instructions.strip()]
        if invocation.goal.strip() and invocation.goal.strip() != invocation.instructions.strip():
            parts.extend(["# Objective", invocation.goal.strip()])

        acceptance_criteria = invocation.metadata.get("acceptance_criteria")
        if acceptance_criteria:
            if isinstance(acceptance_criteria, list):
                criteria = "\n".join(f"- {item}" for item in acceptance_criteria)
            else:
                criteria = str(acceptance_criteria)
            parts.extend(["# Acceptance Criteria", criteria])

        return "\n\n".join(parts)
