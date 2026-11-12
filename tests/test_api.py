from fastapi.testclient import TestClient

from app.api.app import create_app
from app.application.service import TaskService
from app.infrastructure.memory_store import InMemoryTaskStore


class SpyTelemetry:
    """Telemetria espiã: registra as chamadas de RED para asserção nos testes."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str, int]] = []

    def record_request(self, method, route, status, duration_ms):
        self.requests.append((method, route, status))

    def start_span(self, name):
        return _SpySpan()


class _SpySpan:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def set_attribute(self, key, value):
        return None


def _client() -> tuple[TestClient, SpyTelemetry]:
    tel = SpyTelemetry()
    app = create_app(TaskService(InMemoryTaskStore(), tel), tel)
    return TestClient(app), tel


def test_health():
    client, _ = _client()
    assert client.get("/health").json() == {"status": "ok"}


def test_openapi_available():
    client, _ = _client()
    assert client.get("/openapi.json").status_code == 200


def test_create_and_complete_records_metrics():
    client, tel = _client()

    created = client.post("/tasks", json={"title": "estudar OTel"})
    assert created.status_code == 201
    task_id = created.json()["id"]

    assert client.get("/tasks").json()[0]["id"] == task_id

    completed = client.post(f"/tasks/{task_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["done"] is True

    # o middleware registrou RED para cada rota chamada
    routes = [r[1] for r in tel.requests]
    assert "/tasks" in routes
    assert any(status == 201 for _, _, status in tel.requests)


def test_create_empty_title_returns_400():
    client, _ = _client()
    resp = client.post("/tasks", json={"title": "   "})
    assert resp.status_code == 400
    assert resp.json()["error"]


def test_complete_unknown_returns_404():
    client, _ = _client()
    resp = client.post("/tasks/inexistente/complete")
    assert resp.status_code == 404


def test_unknown_route_still_measured():
    client, tel = _client()
    assert client.get("/nao-existe").status_code == 404
    assert tel.requests  # middleware mediu mesmo a rota 404


def test_unhandled_failure_is_measured_as_500():
    telemetry = SpyTelemetry()
    app = create_app(TaskService(InMemoryTaskStore(), telemetry), telemetry)

    @app.get("/broken")
    def broken():
        raise RuntimeError("unexpected failure")

    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/broken").status_code == 500
    assert telemetry.requests == [("GET", "/broken", 500)]


def test_unmatched_urls_share_a_bounded_label():
    client, telemetry = _client()
    assert client.get("/unknown-one").status_code == 404
    assert client.get("/unknown-two").status_code == 404
    assert telemetry.requests == [("GET", "<unmatched>", 404)] * 2


def test_route_parameters_are_not_metric_labels():
    client, telemetry = _client()
    client.post("/tasks/first/complete")
    client.post("/tasks/second/complete")
    assert telemetry.requests == [("POST", "/tasks/{task_id}/complete", 404)] * 2
