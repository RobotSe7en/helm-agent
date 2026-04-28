from __future__ import annotations

from helm.tools.base import Tool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        name = self._internal_name(name)
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    def schemas_for(self, names: list[str]) -> list[dict[str, object]]:
        schemas: list[dict[str, object]] = []
        for name in names:
            tool = self.get(name)
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": self._external_name(tool.name),
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )
        return schemas

    def _external_name(self, name: str) -> str:
        return name.replace(".", "_")

    def _internal_name(self, name: str) -> str:
        if name in self._tools:
            return name
        dotted = name.replace("_", ".")
        if dotted in self._tools:
            return dotted
        return name
