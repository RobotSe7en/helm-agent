from __future__ import annotations

from dataclasses import asdict

from helm.taskgraph.models import Run, TaskGraph


def task_graph_to_dict(graph: TaskGraph) -> dict[str, object]:
    return asdict(graph)


def run_to_dict(run: Run) -> dict[str, object]:
    return asdict(run)
