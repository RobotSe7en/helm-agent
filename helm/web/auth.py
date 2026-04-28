from __future__ import annotations


class LocalAuth:
    def is_allowed(self, user_id: str | None) -> bool:
        return True
