import pytest

from app.application.service import TaskService
from app.domain.errors import NotFoundError
from app.infrastructure.memory_store import InMemoryTaskStore
from app.infrastructure.noop_telemetry import NoopTelemetry


def _service() -> TaskService:
    return TaskService(InMemoryTaskStore(), NoopTelemetry())


def test_create_list_complete_flow():
    svc = _service()
    a = svc.create("primeira")
    b = svc.create("segunda")
    assert a.id == "task-1" and b.id == "task-2"
    assert {t.id for t in svc.list()} == {"task-1", "task-2"}

    done = svc.complete("task-1")
    assert done.done is True


def test_complete_unknown_raises_not_found():
    with pytest.raises(NotFoundError):
        _service().complete("task-999")


def test_store_get_missing_returns_none():
    assert InMemoryTaskStore().get("nope") is None


def test_noop_telemetry_is_inert():
    tel = NoopTelemetry()
    tel.record_request("GET", "/x", 200, 1.5)
    with tel.start_span("op") as span:
        span.set_attribute("k", "v")
