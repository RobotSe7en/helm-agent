from __future__ import annotations

import asyncio
from pathlib import Path

from helm.config.settings import Settings
from helm.run_service import RunService
from helm.taskgraph.models import RunStatus, TaskStatus


def test_run_service_smoke() -> None:
    workspace = Path.cwd() / ".test-workspace"
    workspace.mkdir(exist_ok=True)
    service = RunService(Settings(project_root=workspace))
    run = asyncio.run(service.run_goal("Smoke test the backbone."))

    assert run.status == RunStatus.COMPLETED
    assert run.task_graph is not None
    assert [task.status for task in run.task_graph.tasks] == [
        TaskStatus.COMPLETED,
        TaskStatus.COMPLETED,
    ]
    assert run.final_result
