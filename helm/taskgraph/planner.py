from __future__ import annotations

from helm.taskgraph.models import Run, RunStatus, Task, TaskGraph


class SimpleTaskGraphPlanner:
    """Small v0 planner that creates a stable two-step graph.

    A model-backed planner can replace this later without changing the
    TaskGraphExecutor contract.
    """

    def plan(self, run: Run) -> TaskGraph:
        run.status = RunStatus.PLANNING
        planning = Task(
            title="Clarify execution plan",
            description=f"Turn the user goal into a concise execution approach: {run.goal}",
            assignee="planner",
            skills=["task-planning"],
            acceptance_criteria=["The plan is concrete enough for execution."],
        )
        execution = Task(
            title="Execute user goal",
            description=run.goal,
            assignee="executor",
            skills=["code-execution"],
            depends_on=[planning.id],
            acceptance_criteria=["The requested outcome is completed or clearly blocked."],
        )
        graph = TaskGraph(run_id=run.id, tasks=[planning, execution])
        run.task_graph = graph
        return graph
