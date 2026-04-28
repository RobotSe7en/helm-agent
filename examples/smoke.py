from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from helm.config.settings import Settings
from helm.run_service import RunService


async def main() -> None:
    service = RunService(Settings(project_root=Path.cwd()))
    run = await service.run_goal("Create the minimal Helm Agent v0.0.1 backbone.")
    print(f"run_id={run.id}")
    print(f"status={run.status}")
    if run.task_graph:
        for task in run.task_graph.tasks:
            print(f"- {task.status}: {task.title} -> {task.result}")


if __name__ == "__main__":
    asyncio.run(main())
