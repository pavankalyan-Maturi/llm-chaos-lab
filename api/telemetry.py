"""OpenTelemetry setup.

GenAI semantic conventions are still Development status. The opt-in is pinned
via OTEL_SEMCONV_STABILITY_OPT_IN in docker-compose.yml. Message content
capture is OFF by default: spans carry token counts and references, not
prompts.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from api.settings import Settings

_configured = False


def setup_tracing(settings: Settings) -> None:
    global _configured
    if _configured or not settings.otel_enabled:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": settings.service_name}))
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{settings.otlp_endpoint}/v1/traces"))
    )
    trace.set_tracer_provider(provider)
    _configured = True


tracer = trace.get_tracer("llm-chaos-lab")
