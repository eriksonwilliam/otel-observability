from __future__ import annotations

import os

from app.api.app import create_app
from app.application.service import TaskService
from app.infrastructure.memory_store import InMemoryTaskStore


def build_telemetry():  # pragma: no cover
    if os.getenv("TELEMETRY") == "otel":
        from app.infrastructure.otel_telemetry import OtelTelemetry

        return OtelTelemetry()
    from app.infrastructure.noop_telemetry import NoopTelemetry

    return NoopTelemetry()


telemetry = build_telemetry()  # pragma: no cover
app = create_app(TaskService(InMemoryTaskStore(), telemetry), telemetry)  # pragma: no cover
