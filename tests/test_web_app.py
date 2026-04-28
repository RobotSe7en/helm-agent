from __future__ import annotations

from fastapi.testclient import TestClient

from helm.web.api.app import create_app


def test_web_health_and_index() -> None:
    client = TestClient(create_app())

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    index = client.get("/")
    assert index.status_code == 200
    assert "Helm Agent" in index.text


def test_model_test_api_uses_request_config(monkeypatch) -> None:
    from helm.runtime.result import RuntimeResult
    from helm.web.api import app as app_module

    seen = {}

    class FakeRuntime:
        async def invoke(self, invocation):
            seen["invocation"] = invocation
            return RuntimeResult(status="completed", output="ok")

    def capture_runtime(settings):
        seen["settings"] = settings
        return FakeRuntime()

    monkeypatch.setattr(app_module, "create_runtime", capture_runtime)
    client = TestClient(create_app())

    response = client.post(
        "/api/model/test",
        json={
            "base_url": "http://example.test/v1",
            "model": "custom-model",
            "api_key": "secret",
            "provider": "test-provider",
            "prompt": "Say hello.",
            "max_tokens": 32,
            "temperature": 0.1,
            "enable_thinking": False,
        },
    )

    assert response.status_code == 200
    provider = seen["settings"].providers["test-provider"]
    assert provider.base_url == "http://example.test/v1"
    assert provider.model == "custom-model"
    assert provider.api_key == "secret"
    assert seen["invocation"].profile == "default"
    assert seen["invocation"].provider == "test-provider"
    assert response.json()["output"] == "ok"


def test_web_config_hides_api_key(monkeypatch) -> None:
    from helm.config.settings import ProviderConfig, Settings
    from helm.web.api import app as app_module

    monkeypatch.setattr(
        app_module.Settings,
        "load",
        classmethod(
            lambda cls: Settings(
                default_provider="test-provider",
                providers={
                    "test-provider": ProviderConfig(
                        id="test-provider",
                        base_url="http://example.test/v1",
                        model="custom-model",
                        api_key="secret",
                    )
                },
            )
        ),
    )
    client = TestClient(create_app())

    response = client.get("/api/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"]["has_api_key"] is True
    assert "secret" not in response.text


def test_chat_api_uses_requested_toolsets_without_profile_override(monkeypatch) -> None:
    from helm.runtime.result import RuntimeResult
    from helm.web.api import app as app_module

    seen = {}

    class FakeRuntime:
        async def invoke(self, invocation):
            seen["invocation"] = invocation
            return RuntimeResult(status="completed", output="hello")

    monkeypatch.setattr(app_module, "create_runtime", lambda settings: FakeRuntime())
    client = TestClient(create_app())

    response = client.post(
        "/api/chat",
        json={
            "provider": "test-provider",
            "base_url": "http://example.test/v1",
            "model": "custom-model",
            "api_key": "secret",
            "prompt": "hello",
            "toolsets": ["filesystem"],
        },
    )

    assert response.status_code == 200
    assert response.json()["output"] == "hello"
    assert seen["invocation"].goal == "Conversation"
    assert seen["invocation"].task_id is None
    assert seen["invocation"].toolsets == ["filesystem"]
    assert seen["invocation"].profile_obj is None


def test_chat_stream_returns_tool_and_delta_events(monkeypatch) -> None:
    from helm.runtime.result import RuntimeResult
    from helm.web.api import app as app_module

    class FakeRuntime:
        async def invoke(self, invocation):
            return RuntimeResult(
                status="completed",
                output="hello **markdown**",
                events=[
                    {
                        "type": "tool.completed",
                        "tool": "filesystem_list",
                        "arguments": {"path": "."},
                        "ok": True,
                        "content": "file\tREADME.md",
                    }
                ],
            )

    monkeypatch.setattr(app_module, "create_runtime", lambda settings: FakeRuntime())
    client = TestClient(create_app())

    response = client.post(
        "/api/chat/stream",
        json={
            "provider": "test-provider",
            "base_url": "http://example.test/v1",
            "model": "custom-model",
            "api_key": "secret",
            "prompt": "List files.",
            "toolsets": ["filesystem"],
        },
    )

    assert response.status_code == 200
    assert '"type": "tool"' in response.text
    assert "filesystem_list" in response.text
    assert '"type": "delta"' in response.text
    assert "hello **markdown**" in response.text
    assert '"type": "done"' in response.text


def test_chat_stream_uses_provider_stream_without_tools(monkeypatch) -> None:
    from helm.providers.base import ChatMessage
    from helm.providers.registry import ProviderRegistry
    from helm.providers.resolver import ProviderResolver
    from helm.runtime.loop import RuntimeLoop
    from helm.web.api import app as app_module

    class StreamingProvider:
        id = "streaming"

        async def complete(self, messages: list[ChatMessage], **kwargs):
            raise AssertionError("complete should not be used for tool-free streaming")

        async def stream(self, messages: list[ChatMessage], **kwargs):
            yield "hello "
            yield "**markdown**"

    original_create_runtime = app_module.create_runtime

    def fake_runtime(settings):
        registry = ProviderRegistry()
        registry.register(StreamingProvider())
        return RuntimeLoop(
            context_builder=original_create_runtime(settings).context_builder,
            provider_resolver=ProviderResolver(registry, settings),
        )

    monkeypatch.setattr(app_module, "create_runtime", fake_runtime)
    client = TestClient(create_app())

    response = client.post(
        "/api/chat/stream",
        json={
            "provider": "streaming",
            "base_url": "http://example.test/v1",
            "model": "custom-model",
            "api_key": "secret",
            "prompt": "hello",
        },
    )

    assert response.status_code == 200
    assert '"type": "delta", "content": "hello "' in response.text
    assert '"type": "delta", "content": "**markdown**"' in response.text
    assert '"provider": "streaming"' in response.text


def test_model_test_api_passes_profile_skills_and_toolsets(monkeypatch) -> None:
    from helm.runtime.result import RuntimeResult
    from helm.web.api import app as app_module

    seen = {}

    class FakeRuntime:
        async def invoke(self, invocation):
            seen["invocation"] = invocation
            return RuntimeResult(status="completed", output="ok")

    monkeypatch.setattr(app_module, "create_runtime", lambda settings: FakeRuntime())
    client = TestClient(create_app())

    response = client.post(
        "/api/model/test",
        json={
            "base_url": "http://example.test/v1",
            "model": "custom-model",
            "api_key": "secret",
            "profile": "reviewer",
            "skills": ["code-review"],
            "toolsets": ["filesystem", "git"],
            "prompt": "Review this.",
            "max_tokens": 32,
            "temperature": 0.1,
            "enable_thinking": False,
        },
    )

    assert response.status_code == 200
    assert seen["invocation"].profile == "reviewer"
    assert seen["invocation"].skills == ["code-review"]
    assert seen["invocation"].toolsets == ["filesystem", "git"]


def test_model_test_api_returns_json_for_runtime_errors(monkeypatch) -> None:
    from helm.web.api import app as app_module

    class BrokenRuntime:
        async def invoke(self, invocation):
            raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "create_runtime", lambda settings: BrokenRuntime())
    client = TestClient(create_app())

    response = client.post(
        "/api/model/test",
        json={
            "base_url": "http://example.test/v1",
            "model": "custom-model",
            "api_key": "secret",
            "prompt": "Say hello.",
            "max_tokens": 32,
            "temperature": 0.1,
            "enable_thinking": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["events"][0]["type"] == "runtime.failed"
    assert "RuntimeError" in payload["error"]
