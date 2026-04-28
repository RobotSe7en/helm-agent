from __future__ import annotations

from helm.runtime.invocation import RuntimeInvocation
from helm.runtime.loop import RuntimeLoop
from helm.taskgraph.models import Run, RunStatus, TaskStatus


class TaskGraphExecutor:
    def __init__(self, runtime: RuntimeLoop):
        self.runtime = runtime

    async def execute(self, run: Run) -> Run:
        if run.task_graph is None:
            raise ValueError("Run has no task graph")

        run.status = RunStatus.RUNNING
        while run.task_graph.has_pending_tasks():
            ready = run.task_graph.ready_tasks()
            if not ready:
                run.status = RunStatus.FAILED
                raise RuntimeError("Task graph is blocked; no ready tasks remain")

            task = ready[0]
            task.status = TaskStatus.RUNNING
            result = await self.runtime.invoke(
                RuntimeInvocation(
                    run_id=run.id,
                    task_id=task.id,
                    profile=task.assignee,
                    goal=task.title,
                    instructions=task.description,
                    skills=task.skills,
                    metadata={"acceptance_criteria": task.acceptance_criteria},
                )
            )
            if result.status == "completed":
                task.status = TaskStatus.COMPLETED
                task.result = result.output
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error or result.output
                run.status = RunStatus.FAILED
                return run

        run.status = RunStatus.COMPLETED
        run.final_result = "\n\n".join(
            task.result or "" for task in run.task_graph.tasks if task.result
        )
        return run
