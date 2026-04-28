from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

import yaml


@dataclass(slots=True)
class ProviderConfig:
    id: str
    type: str = "openai-compatible"
    base_url: str = "http://192.168.1.18:16666/v1"
    model: str = "qwen3"
    api_key: str = "EMPTY"
    api_key_env: str | None = None
    timeout_seconds: int = 120

    def resolved_api_key(self) -> str:
        if self.api_key_env:
            return os.environ.get(self.api_key_env, self.api_key)
        return self.api_key


@dataclass(slots=True)
class Settings:
    project_root: Path = Path.cwd()
    profile_dir: Path = Path("profiles")
    skill_dir: Path = Path("skills")
    store_path: Path = Path(".helm/helm.db")
    default_profile: str = "default"
    default_provider: str = "echo"
    providers: dict[str, ProviderConfig] = field(
        default_factory=lambda: {
            "minimax": ProviderConfig(id="minimax"),
        }
    )
    require_plan_approval: bool = False
    max_runtime_iterations: int = 8
    max_child_delegations: int = 3
    max_delegation_depth: int = 1

    @classmethod
    def load(
        cls,
        path: str | Path = "helm.yaml",
        env_path: str | Path = ".env",
    ) -> "Settings":
        project_root = Path.cwd()
        config_path = Path(path)
        if not config_path.is_absolute():
            config_path = project_root / config_path
        env_file = Path(env_path)
        if not env_file.is_absolute():
            env_file = project_root / env_file

        _load_env_file(env_file)
        if not config_path.exists():
            return cls(project_root=project_root)

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        settings = cls(project_root=project_root)
        for key, value in data.items():
            if key == "providers":
                settings.providers = _load_provider_configs(value)
                continue
            if hasattr(settings, key):
                if key.endswith("_dir") or key.endswith("_path") or key == "project_root":
                    value = Path(value)
                    if not value.is_absolute() and key == "project_root":
                        value = (config_path.parent / value).resolve()
                setattr(settings, key, value)
        return settings

    def resolve_project_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return self.project_root / path


def load_settings(path: str | Path = "helm.yaml") -> Settings:
    return Settings.load(path)


def _load_provider_configs(raw: object) -> dict[str, ProviderConfig]:
    if not isinstance(raw, dict):
        raise ValueError("providers must be a mapping")
    providers: dict[str, ProviderConfig] = {}
    for provider_id, provider_data in raw.items():
        if provider_data is None:
            provider_data = {}
        if not isinstance(provider_data, dict):
            raise ValueError(f"provider config must be a mapping: {provider_id}")
        data = dict(provider_data)
        data.setdefault("id", str(provider_id))
        providers[str(provider_id)] = ProviderConfig(**data)
    return providers


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
