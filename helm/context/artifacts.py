from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Artifact:
    path: Path
    kind: str = "file"
    description: str = ""
