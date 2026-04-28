from __future__ import annotations

from helm.app import create_runtime
from helm.config.settings import Settings
from helm.taskgraph.executor import TaskGraphExecutor
from helm.taskgraph.models import Run
from helm.taskgraph.planner import SimpleTaskGraphPlanner


class RunService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.runtime = create_runtime(self.settings)
        self.planner = SimpleTaskGraphPlanner()
        self.executor = TaskGraphExecutor(self.runtime)

    async def run_goal(self, goal: str) -> Run:
        run = Run(goal=goal)
        self.planner.plan(run)
        return await self.executor.execute(run)
