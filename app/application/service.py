from __future__ import annotations

from app.application.ports import TaskStore, Telemetry
from app.domain.errors import NotFoundError
from app.domain.task import Task, new_task


class TaskService:
    """Casos de uso de tarefas, cada operação envolvida num span de trace."""

    def __init__(self, store: TaskStore, telemetry: Telemetry) -> None:
        self._store = store
        self._telemetry = telemetry
        self._seq = 0

    def create(self, title: str) -> Task:
        with self._telemetry.start_span("task.create") as span:
            self._seq += 1
            task = new_task(f"task-{self._seq}", title)
            span.set_attribute("task.id", task.id)
            self._store.put(task)
            return task

    def list(self) -> list[Task]:
        with self._telemetry.start_span("task.list"):
            return self._store.all()

    def complete(self, task_id: str) -> Task:
        with self._telemetry.start_span("task.complete") as span:
            span.set_attribute("task.id", task_id)
            task = self._store.get(task_id)
            if task is None:
                raise NotFoundError(task_id)
            task.complete()
            self._store.put(task)
            return task
