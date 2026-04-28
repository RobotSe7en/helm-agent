from __future__ import annotations

from pathlib import Path

import pytest

from helm.config.settings import Settings
from helm.context.context_builder import ContextBuilder
from helm.context.prompt_builder import PromptBuilder
from helm.profiles.loader import ProfileLoader
from helm.profiles.registry import ProfileRegistry
from helm.providers.base import ChatMessage, ProviderResponse, ToolCall
from helm.providers.registry import ProviderRegistry
from helm.providers.resolver import ProviderResolver
from helm.runtime.invocation import RuntimeInvocation
from helm.runtime.loop import RuntimeLoop
from helm.runtime.tool_dispatcher import ToolDispatcher
from helm.skills.loader import SkillLoader
from helm.skills.registry import SkillRegistry
from helm.tools.filesystem import FileListTool, FileReadTool, FileWriteTool
from helm.tools.git import GitDiffTool, GitStatusTool
from helm.tools.registry import ToolRegistry
from helm.tools.shell import ShellRunTool


class SequencedProvider:
    id = "sequenced"

    def __init__(self, responses: list[ProviderResponse]):
        self.responses = responses
        self.messages_by_call: list[list[ChatMessage]] = []

    async def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: object,
    ) -> ProviderResponse:
        self.messages_by_call.append(list(messages))
        return self.responses[len(self.messages_by_call) - 1]


def make_context_builder(project_root: Path) -> ContextBuilder:
    settings = Settings(project_root=project_root)
    return ContextBuilder(
        profile_registry=ProfileRegistry(
            ProfileLoader(settings.resolve_project_path(settings.profile_dir))
        ),
        skill_registry=SkillRegistry(
            SkillLoader(settings.resolve_project_path(settings.skill_dir))
        ),
        prompt_builder=PromptBuilder(),
    )


def test_context_builder_injects_profile_and_skill() -> None:
    builder = make_context_builder(Path.cwd())

    messages = builder.build_messages(
        RuntimeInvocation(
            run_id="test",
            task_id="task",
            profile="planner",
            goal="Plan",
            instructions="Create a plan.",
        )
    )

    assert "You turn goals into concrete" in messages[0].content
    assert "Task Planning Skill" in messages[0].content


def test_context_builder_user_context_hides_internal_ids() -> None:
    builder = make_context_builder(Path.cwd())

    messages = builder.build_messages(
        RuntimeInvocation(
            run_id="web",
            task_id="web_chat_message",
            profile="default",
            goal="Conversation",
            instructions="hello",
        )
    )

    assert "# User Request" in messages[1].content
    assert "hello" in messages[1].content
    assert "web_chat_message" not in messages[1].content
    assert "Run:" not in messages[1].content


def test_tool_registry_exports_openai_compatible_schema_names() -> None:
    registry = ToolRegistry()
    registry.register(FileReadTool(Path.cwd()))

    schemas = registry.schemas_for(["filesystem.read"])

    assert schemas[0]["function"]["name"] == "filesystem_read"
    assert registry.get("filesystem_read").name == "filesystem.read"


@pytest.mark.asyncio
async def test_filesystem_list_tool_lists_project_entries(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "nested").mkdir()

    result = await FileListTool(tmp_path).run(path=".")

    assert result.ok
    assert "file\talpha.txt" in result.content
    assert "dir\tnested" in result.content


@pytest.mark.asyncio
async def test_runtime_events_include_profile_skills_and_tools() -> None:
    settings = Settings(project_root=Path.cwd())
    tool_registry = ToolRegistry()
    tool_registry.register(FileListTool(Path.cwd()))
    tool_registry.register(FileReadTool(Path.cwd()))
    tool_registry.register(FileWriteTool(Path.cwd()))
    tool_registry.register(ShellRunTool(Path.cwd()))
    tool_registry.register(GitStatusTool(Path.cwd()))
    tool_registry.register(GitDiffTool(Path.cwd()))
    runtime = RuntimeLoop(
        context_builder=make_context_builder(Path.cwd()),
        provider_resolver=ProviderResolver(ProviderRegistry(), settings),
        tool_dispatcher=ToolDispatcher(tool_registry),
    )

    result = await runtime.invoke(
        RuntimeInvocation(
            run_id="test",
            profile="executor",
            goal="List files",
            instructions="List files.",
            skills=["code-execution"],
            toolsets=["filesystem.list"],
        )
    )

    started = result.events[0]
    assert started["type"] == "runtime.started"
    assert started["profile"] == "executor"
    assert "code-execution" in started["skills"]
    assert "filesystem_list" in started["tools"]


@pytest.mark.asyncio
async def test_runtime_continues_tool_loop_until_provider_finishes(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("hello from alpha", encoding="utf-8")
    settings = Settings(project_root=tmp_path)
    provider = SequencedProvider(
        [
            ProviderResponse(
                content="",
                tool_calls=[ToolCall("filesystem_list", {"path": "."})],
            ),
            ProviderResponse(
                content="",
                tool_calls=[ToolCall("filesystem_read", {"path": "alpha.txt"})],
            ),
            ProviderResponse(content="done after tools"),
        ]
    )
    provider_registry = ProviderRegistry()
    provider_registry.register(provider)
    tool_registry = ToolRegistry()
    tool_registry.register(FileListTool(tmp_path))
    tool_registry.register(FileReadTool(tmp_path))
    tool_registry.register(FileWriteTool(tmp_path))
    tool_registry.register(GitStatusTool(tmp_path))
    tool_registry.register(GitDiffTool(tmp_path))
    runtime = RuntimeLoop(
        context_builder=make_context_builder(tmp_path),
        provider_resolver=ProviderResolver(provider_registry, settings),
        tool_dispatcher=ToolDispatcher(tool_registry),
    )

    result = await runtime.invoke(
        RuntimeInvocation(
            run_id="test",
            profile="default",
            goal="Use two tools",
            instructions="List files, then read alpha.",
            provider="sequenced",
            toolsets=["filesystem.list", "filesystem.read"],
        )
    )

    provider_events = [
        event for event in result.events if event["type"] == "provider.completed"
    ]
    tool_events = [
        event for event in result.events if event["type"] == "tool.completed"
    ]
    assert result.status == "completed"
    assert result.output == "done after tools"
    assert [event["iteration"] for event in provider_events] == [1, 2, 3]
    assert [event["tool"] for event in tool_events] == [
        "filesystem_list",
        "filesystem_read",
    ]
    assert "alpha.txt" in provider.messages_by_call[1][-1].content
    assert "hello from alpha" in provider.messages_by_call[2][-1].content
