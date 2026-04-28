from __future__ import annotations

from helm.providers.openai_compatible import OpenAICompatibleProvider


def test_parse_openai_compatible_text_response() -> None:
    provider = OpenAICompatibleProvider(
        id="test-openai",
        base_url="http://example.test/v1",
        api_key="EMPTY",
        model="qwen3",
    )

    response = provider._parse_response(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "ok",
                    }
                }
            ]
        }
    )

    assert response.content == "ok"
    assert response.tool_calls == []


def test_parse_openai_compatible_tool_call_response() -> None:
    provider = OpenAICompatibleProvider(
        id="test-openai",
        base_url="http://example.test/v1",
        api_key="EMPTY",
        model="qwen3",
    )

    response = provider._parse_response(
        {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "filesystem.read",
                                    "arguments": "{\"path\": \"README.md\"}",
                                }
                            }
                        ]
                    }
                }
            ]
        }
    )

    assert response.tool_calls[0].name == "filesystem.read"
    assert response.tool_calls[0].arguments == {"path": "README.md"}
