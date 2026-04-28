from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class RunStatus(StrEnum):
    CREATED = "created"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass(slots=True)
class Task:
    title: str
    description: str
    id: str = field(default_factory=lambda: new_id("task"))
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    assignee: str = "executor"
    skills: list[str] = field(default_factory=list)
    risk: str = "medium"
    requires_approval: bool = False
    result: str | None = None
    error: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED,
        }


@dataclass(slots=True)
class TaskGraph:
    run_id: str
    tasks: list[Task] = field(default_factory=list)

    def task_by_id(self, task_id: str) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"Unknown task id: {task_id}")

    def ready_tasks(self) -> list[Task]:
        completed = {
            task.id for task in self.tasks if task.status == TaskStatus.COMPLETED
        }
        return [
            task
            for task in self.tasks
            if task.status == TaskStatus.PENDING
            and all(dep_id in completed for dep_id in task.depends_on)
        ]

    def has_pending_tasks(self) -> bool:
        return any(task.status == TaskStatus.PENDING for task in self.tasks)

    def all_done(self) -> bool:
        return all(task.status == TaskStatus.COMPLETED for task in self.tasks)


@dataclass(slots=True)
class Run:
    goal: str
    id: str = field(default_factory=lambda: new_id("run"))
    status: RunStatus = RunStatus.CREATED
    task_graph: TaskGraph | None = None
    final_result: str | None = None
    feedback: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
