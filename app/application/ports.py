from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.task import Task


@runtime_checkable
class TaskStore(Protocol):
    def put(self, task: Task) -> None: ...
    def get(self, task_id: str) -> Task | None: ...
    def all(self) -> list[Task]: ...


class Span(Protocol):
    """Um span de trace ativo (context manager)."""

    def __enter__(self) -> Span: ...
    def __exit__(self, *exc: object) -> None: ...
    def set_attribute(self, key: str, value: object) -> None: ...


@runtime_checkable
class Telemetry(Protocol):
    """Porta de observabilidade: métricas RED + tracing."""

    def record_request(self, method: str, route: str, status: int, duration_ms: float) -> None: ...

    def start_span(self, name: str) -> Span: ...
