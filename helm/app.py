from __future__ import annotations

from pathlib import Path

from helm.config.settings import Settings
from helm.context.context_builder import ContextBuilder
from helm.context.prompt_builder import PromptBuilder
from helm.profiles.loader import ProfileLoader
from helm.profiles.registry import ProfileRegistry
from helm.providers.registry import ProviderRegistry
from helm.providers.resolver import ProviderResolver
from helm.providers.openai_compatible import OpenAICompatibleProvider
from helm.runtime.loop import RuntimeLoop
from helm.runtime.tool_dispatcher import ToolDispatcher
from helm.skills.loader import SkillLoader
from helm.skills.registry import SkillRegistry
from helm.tools.filesystem import FileListTool, FileReadTool, FileWriteTool
from helm.tools.git import GitDiffTool, GitStatusTool
from helm.tools.registry import ToolRegistry
from helm.tools.shell import ShellRunTool


def create_runtime(settings: Settings | None = None) -> RuntimeLoop:
    settings = settings or Settings()
    project_root = settings.project_root

    profile_registry = ProfileRegistry(
        ProfileLoader(settings.resolve_project_path(settings.profile_dir))
    )
    skill_registry = SkillRegistry(
        SkillLoader(settings.resolve_project_path(settings.skill_dir))
    )
    context_builder = ContextBuilder(
        profile_registry=profile_registry,
        skill_registry=skill_registry,
        prompt_builder=PromptBuilder(),
    )
    provider_registry = ProviderRegistry()
    for provider_config in settings.providers.values():
        if provider_config.type != "openai-compatible":
            raise ValueError(
                f"Unsupported provider type for {provider_config.id}: "
                f"{provider_config.type}"
            )
        provider_registry.register(
            OpenAICompatibleProvider(
                id=provider_config.id,
                base_url=provider_config.base_url,
                api_key=provider_config.resolved_api_key(),
                model=provider_config.model,
                timeout_seconds=provider_config.timeout_seconds,
            )
        )
    provider_resolver = ProviderResolver(provider_registry, settings)

    tool_registry = ToolRegistry()
    tool_registry.register(FileListTool(Path(project_root)))
    tool_registry.register(FileReadTool(Path(project_root)))
    tool_registry.register(FileWriteTool(Path(project_root)))
    tool_registry.register(ShellRunTool(Path(project_root)))
    tool_registry.register(GitStatusTool(Path(project_root)))
    tool_registry.register(GitDiffTool(Path(project_root)))

    return RuntimeLoop(
        context_builder=context_builder,
        provider_resolver=provider_resolver,
        tool_dispatcher=ToolDispatcher(tool_registry),
        max_iterations=settings.max_runtime_iterations,
    )
