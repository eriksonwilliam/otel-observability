from __future__ import annotations

from app.domain.task import Task


class InMemoryTaskStore:
    """Read/write store de tarefas em memória."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def put(self, task: Task) -> None:
        self._tasks[task.id] = task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def all(self) -> list[Task]:
        return list(self._tasks.values())
