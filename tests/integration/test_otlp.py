"""Opt-in real OTLP export to a local gRPC receiver (not the Docker stack)."""

import os
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import pytest

pytestmark = pytest.mark.skipif(os.getenv("RUN_OTLP_INTEGRATION") != "1", reason="opt-in OTLP test")


def test_real_exporter_sends_metrics_and_spans(monkeypatch):
    monkeypatch.setenv("OTEL_TRACES_SAMPLER", "always_on")
    import grpc
    from opentelemetry import metrics, trace
    from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2 as mp
    from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2_grpc as mg
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2 as tp
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2_grpc as tg

    from app.infrastructure.otel_telemetry import OtelTelemetry

    received_metrics, received_traces = Queue(), Queue()

    class MetricsReceiver(mg.MetricsServiceServicer):
        def Export(self, request, context):
            received_metrics.put(request)
            return mp.ExportMetricsServiceResponse()

    class TraceReceiver(tg.TraceServiceServicer):
        def Export(self, request, context):
            received_traces.put(request)
            return tp.ExportTraceServiceResponse()

    server = grpc.server(ThreadPoolExecutor(max_workers=2))
    mg.add_MetricsServiceServicer_to_server(MetricsReceiver(), server)
    tg.add_TraceServiceServicer_to_server(TraceReceiver(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    try:
        telemetry = OtelTelemetry(f"http://127.0.0.1:{port}")
        with telemetry.start_span("integration.operation"):
            telemetry.record_request("GET", "/tasks/{task_id}", 500, 12.5)
        assert metrics.get_meter_provider().force_flush(timeout_millis=5000)
        assert trace.get_tracer_provider().force_flush(timeout_millis=5000)
        exported = received_metrics.get(timeout=5)
        metric_list = [
            m for r in exported.resource_metrics for s in r.scope_metrics for m in s.metrics
        ]
        assert {m.name for m in metric_list} >= {"http_requests_total", "http_request_duration_ms"}
        counter = next(m for m in metric_list if m.name == "http_requests_total")
        point = counter.sum.data_points[0]
        assert point.as_int == 1
        assert {a.key: a.value.string_value for a in point.attributes} == {
            "method": "GET",
            "route": "/tasks/{task_id}",
            "status": "500",
        }
        exported_trace = received_traces.get(timeout=5)
        assert any(
            s.name == "integration.operation"
            for r in exported_trace.resource_spans
            for scope in r.scope_spans
            for s in scope.spans
        )
    finally:
        metrics.get_meter_provider().shutdown()
        trace.get_tracer_provider().shutdown()
        server.stop(0).wait()
