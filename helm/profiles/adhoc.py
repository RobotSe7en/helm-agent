from __future__ import annotations

from pathlib import Path

from helm.profiles.schema import AgentProfile


def create_adhoc_profile(goal: str, toolsets: list[str] | None = None) -> AgentProfile:
    return AgentProfile(
        id="adhoc",
        name="Ad-hoc Child Agent",
        root=Path("<adhoc>"),
        profile=(
            "You are a focused child agent. Complete only the delegated goal, "
            "use only the provided context, and return a concise summary."
        ),
        soul="Prefer narrow, evidence-backed answers. Do not ask the user questions.",
        memory="",
        default_toolsets=toolsets or [],
        max_iterations=4,
    )
