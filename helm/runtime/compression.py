from __future__ import annotations


class CompressionManager:
    def compress(self, text: str, limit: int = 8000) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 32] + "\n...[compressed]"
