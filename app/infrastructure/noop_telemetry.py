from __future__ import annotations


class _NoopSpan:
    def __enter__(self) -> _NoopSpan:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def set_attribute(self, key: str, value: object) -> None:
        return None


class NoopTelemetry:
    """Telemetria que não faz nada — padrão para testes e execução offline."""

    def record_request(self, method: str, route: str, status: int, duration_ms: float) -> None:
        return None

    def start_span(self, name: str) -> _NoopSpan:
        return _NoopSpan()
