from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from helm.app import create_runtime
from helm.config.settings import Settings
from helm.profiles.schema import AgentProfile
from helm.runtime.invocation import RuntimeInvocation


async def main() -> None:
    settings = Settings.load()
    runtime = create_runtime(settings)
    profile = AgentProfile(
        id="smoke",
        name="Smoke Tester",
        root=Path.cwd(),
        profile="You are a connection test assistant. Reply directly and do not call tools.",
        default_toolsets=[],
    )
    result = await runtime.invoke(
        RuntimeInvocation(
            run_id="local_model_smoke",
            task_id="local_model_smoke_task",
            profile="smoke",
            profile_obj=profile,
            goal="Local model smoke test",
            instructions=(
                "Reply with one short sentence confirming the local "
                "OpenAI-compatible provider is working. Do not include reasoning."
            ),
            provider=settings.default_provider,
            metadata={
                "max_tokens": 300,
            },
        )
    )
    print(f"status={result.status}")
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
