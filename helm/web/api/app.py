from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from helm import __version__
from helm.app import create_runtime
from helm.config.settings import ProviderConfig, Settings
from helm.profiles.schema import AgentProfile
from helm.runtime.invocation import RuntimeInvocation


class ChatRequest(BaseModel):
    provider: str = Field(default="minimax")
    base_url: str = Field(default="")
    model: str = Field(default="")
    api_key: str = Field(default="")
    prompt: str = Field(default="Reply with a short confirmation.")
    profile: str = Field(default="default")
    skills: list[str] = Field(default_factory=list)
    toolsets: list[str] = Field(default_factory=list)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.2, ge=0, le=2)
    enable_thinking: bool = False


ModelTestRequest = ChatRequest


def create_app():
    try:
        from fastapi import FastAPI
        from fastapi.responses import FileResponse, HTMLResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:
        raise RuntimeError("Install helm-agent[web] to use the web app") from exc

    app = FastAPI(title="Helm Agent", version=__version__)
    static_root = Path(__file__).resolve().parents[3] / "webui" / "dist"
    assets_root = static_root / "assets"

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/config")
    async def config() -> dict[str, object]:
        settings = Settings.load()
        provider_id = settings.default_provider
        provider = settings.providers.get(provider_id)
        return {
            "version": __version__,
            "default_provider": provider_id,
            "provider": {
                "id": provider_id,
                "base_url": provider.base_url if provider else "",
                "model": provider.model if provider else "",
                "has_api_key": bool(provider and provider.resolved_api_key() != "EMPTY"),
            },
        }

    @app.post("/api/chat")
    async def chat(request: ChatRequest) -> dict[str, object]:
        return await _run_chat(request)

    @app.post("/api/model/test")
    async def test_model(request: ModelTestRequest) -> dict[str, object]:
        return await _run_chat(request)

    if assets_root.exists():
        app.mount("/assets", StaticFiles(directory=assets_root), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_path = static_root / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse(DEV_INDEX_HTML)

    async def _run_chat(request: ChatRequest) -> dict[str, object]:
        try:
            settings = _settings_for_request(request)
            runtime = create_runtime(settings)
            result = await runtime.invoke(
                RuntimeInvocation(
                    run_id="web",
                    task_id=None,
                    profile=request.profile,
                    profile_obj=_chat_profile(request.profile),
                    goal="Conversation",
                    instructions=request.prompt,
                    provider=request.provider,
                    skills=request.skills,
                    toolsets=request.toolsets,
                    metadata={
                        "plain_chat": True,
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                        "extra_body": {
                            "chat_template_kwargs": {
                                "enable_thinking": request.enable_thinking,
                            }
                        },
                    },
                )
            )
        except Exception as exc:
            return {
                "status": "failed",
                "output": "",
                "events": [
                    {
                        "type": "runtime.failed",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                ],
                "error": f"{type(exc).__name__}: {exc}",
                "effective_config": _effective_config(request),
            }
        return {
            "status": result.status,
            "output": result.output,
            "events": result.events,
            "error": result.error,
            "effective_config": _effective_config(request),
        }

    return app


def _settings_for_request(request: ChatRequest) -> Settings:
    settings = Settings.load()
    configured = settings.providers.get(request.provider)
    provider = ProviderConfig(
        id=request.provider,
        base_url=request.base_url or (configured.base_url if configured else ""),
        api_key=request.api_key or (configured.resolved_api_key() if configured else "EMPTY"),
        model=request.model or (configured.model if configured else ""),
        timeout_seconds=configured.timeout_seconds if configured else 120,
    )
    settings.default_provider = request.provider
    settings.providers = {request.provider: provider}
    return settings


def _chat_profile(profile_id: str) -> AgentProfile:
    return AgentProfile(
        id=profile_id,
        name="Chat Agent",
        root=Path.cwd(),
        profile=(
            "You are Helm Agent, a general-purpose AI assistant in a web chat. "
            "Answer the user's message directly in the same language when appropriate. "
            "Do not assume the user is asking about Helm charts unless they say so. "
            "Do not interpret run ids, task ids, or internal labels as user requests."
        ),
        default_toolsets=[],
    )


def _effective_config(request: ChatRequest) -> dict[str, object]:
    return {
        "provider": request.provider,
        "base_url": request.base_url,
        "model": request.model,
        "profile": request.profile,
        "skills": request.skills,
        "toolsets": request.toolsets,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "enable_thinking": request.enable_thinking,
    }


DEV_INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Helm Agent</title>
  </head>
  <body>
    <main style="font-family: system-ui; margin: 40px;">
      <h1>Helm Agent</h1>
      <p>Build the TypeScript Web UI with <code>npm install</code> and <code>npm run build</code> in <code>webui/</code>.</p>
    </main>
  </body>
</html>"""
