from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderCapabilities:
    tool_calling: bool = False
    streaming: bool = False
    vision: bool = False
    json_mode: bool = False
