from __future__ import annotations

import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class OtelTelemetry:
    """Adapter real de observabilidade: métricas RED e traces via OTLP.

    Fora da cobertura (requer o OpenTelemetry Collector). Exporta o contador de
    requisições, o histograma de latência e os spans de cada operação.
    """

    def __init__(self, endpoint: str | None = None) -> None:
        endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        resource = Resource.create({"service.name": "otel-observability"})

        trace.set_tracer_provider(TracerProvider(resource=resource))
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
        )
        self._tracer = trace.get_tracer("otel-observability")

        reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint, insecure=True))
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
        meter = metrics.get_meter("otel-observability")
        self._requests = meter.create_counter(
            "http_requests_total", unit="1", description="Total de requisições HTTP"
        )
        self._latency = meter.create_histogram(
            "http_request_duration_ms", unit="ms", description="Latência das requisições"
        )

    def record_request(self, method: str, route: str, status: int, duration_ms: float) -> None:
        labels = {"method": method, "route": route, "status": str(status)}
        self._requests.add(1, labels)
        self._latency.record(duration_ms, labels)

    def start_span(self, name: str):  # type: ignore[no-untyped-def]
        return self._tracer.start_as_current_span(name)
