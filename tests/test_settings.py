from __future__ import annotations

from helm.config.settings import Settings


def test_settings_loads_provider_configs_from_yaml_and_env(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("HELM_TEST_API_KEY", raising=False)
    (tmp_path / ".env").write_text(
        "HELM_TEST_API_KEY=from-env\n",
        encoding="utf-8",
    )
    (tmp_path / "helm.yaml").write_text(
        """
default_provider: test-provider
providers:
  test-provider:
    type: openai-compatible
    base_url: http://example.test/v1
    model: custom-model
    api_key: fallback
    api_key_env: HELM_TEST_API_KEY
    timeout_seconds: 30
""".lstrip(),
        encoding="utf-8",
    )

    settings = Settings.load(tmp_path / "helm.yaml", tmp_path / ".env")

    provider = settings.providers["test-provider"]
    assert settings.default_provider == "test-provider"
    assert provider.base_url == "http://example.test/v1"
    assert provider.model == "custom-model"
    assert provider.timeout_seconds == 30
    assert provider.resolved_api_key() == "from-env"


def test_settings_env_loader_accepts_utf8_bom(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("HELM_BOM_API_KEY", raising=False)
    (tmp_path / ".env").write_text(
        "HELM_BOM_API_KEY=from-bom-env\n",
        encoding="utf-8-sig",
    )
    (tmp_path / "helm.yaml").write_text(
        """
default_provider: test-provider
providers:
  test-provider:
    api_key: fallback
    api_key_env: HELM_BOM_API_KEY
""".lstrip(),
        encoding="utf-8",
    )

    settings = Settings.load(tmp_path / "helm.yaml", tmp_path / ".env")

    assert settings.providers["test-provider"].resolved_api_key() == "from-bom-env"
