from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.application.ports import Telemetry
from app.application.service import TaskService
from app.domain.errors import NotFoundError, ValidationError


class CreateTask(BaseModel):
    title: str


def create_app(service: TaskService, telemetry: Telemetry) -> FastAPI:
    app = FastAPI(title="otel-observability", version="0.1.0")

    @app.middleware("http")
    async def telemetry_mw(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        route = getattr(request.scope.get("route"), "path", request.url.path)
        telemetry.record_request(request.method, route, response.status_code, duration_ms)
        return response

    @app.exception_handler(ValidationError)
    async def _validation(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"error": "tarefa não encontrada"})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/tasks", status_code=201)
    def create(body: CreateTask) -> dict[str, object]:
        task = service.create(body.title)
        return {"id": task.id, "title": task.title, "done": task.done}

    @app.get("/tasks")
    def list_tasks() -> list[dict[str, object]]:
        return [{"id": t.id, "title": t.title, "done": t.done} for t in service.list()]

    @app.post("/tasks/{task_id}/complete")
    def complete(task_id: str) -> dict[str, object]:
        task = service.complete(task_id)
        return {"id": task.id, "title": task.title, "done": task.done}

    return app
