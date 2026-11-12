"""Smoke test: API -> OTLP -> Collector -> Prometheus, plus Grafana provisioning.

Run after docker compose up --build -d. Does not assert trace storage or visual layout.
"""

import json
import time
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def get_json(url, data=None):
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return json.load(response)


def wait_for(check, timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except (URLError, TimeoutError, OSError):
            pass
        time.sleep(2)
    raise RuntimeError("Stack condition not satisfied within timeout")


def main():
    wait_for(lambda: get_json("http://localhost:8080/health")["status"] == "ok")
    task = get_json("http://localhost:8080/tasks", json.dumps({"title": "otlp-smoke"}).encode())
    get_json(f"http://localhost:8080/tasks/{task['id']}/complete", b"")
    query = urlencode(
        {"query": 'http_requests_total{route="/tasks/{task_id}/complete",status="200"}'}
    )
    samples = wait_for(
        lambda: get_json("http://localhost:9090/api/v1/query?" + query)["data"]["result"]
    )
    assert any(float(s["value"][1]) >= 1 for s in samples)
    wait_for(lambda: get_json("http://localhost:3000/api/health")["database"] == "ok")
    dashboards = wait_for(lambda: get_json("http://localhost:3000/api/search?type=dash-db"))
    assert dashboards, "No provisioned Grafana dashboard"
    print("PASS: route metric reached Prometheus; Grafana has a provisioned dashboard")


if __name__ == "__main__":
    main()
