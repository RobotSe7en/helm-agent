from __future__ import annotations


class MemoryStore:
    def __init__(self):
        self._items: list[str] = []

    def add(self, item: str) -> None:
        self._items.append(item)

    def list(self) -> list[str]:
        return list(self._items)
