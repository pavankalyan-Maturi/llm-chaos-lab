"""Fault-flag monolith entry point.

Routes now: health, a stub /v1/chat (plain and SSE), Prometheus /metrics, and
/chaos. Retrieval, agent, MCP and guards plug in as labs add them.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from api.chaos_routes import router as chaos_router
from api.settings import get_settings
from api.telemetry import setup_tracing, tracer
from gateway.llm_client import Message, StubConfig, StubLLMClient

REQUESTS = Counter("lab_requests_total", "Requests", ["route", "tenant"])
LLM_TOKENS = Counter("lab_llm_tokens_total", "LLM tokens", ["direction", "model", "tenant"])
LLM_LATENCY = Histogram("lab_llm_latency_seconds", "LLM call latency", ["model"])


class ChatRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    messages: list[dict[str, str]]
    max_tokens: int | None = Field(default=None, ge=1, le=4096)


def build_llm():
    s = get_settings()
    if s.llm_backend != "stub":
        raise NotImplementedError(f"LLM backend {s.llm_backend!r} not wired yet")
    return StubLLMClient(StubConfig(ttft_s=s.stub_ttft_s, itl_s=s.stub_itl_s))


def create_app() -> FastAPI:
    settings = get_settings()
    setup_tracing(settings)
    app = FastAPI(title="llm-chaos-lab", version="0.1.0")
    app.state.llm = build_llm()
    app.include_router(chaos_router)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics() -> PlainTextResponse:
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/v1/chat")
    async def chat(req: ChatRequest) -> dict:
        REQUESTS.labels("/v1/chat", req.tenant_id).inc()
        llm = app.state.llm
        msgs = [Message(m["role"], m["content"]) for m in req.messages]
        with tracer.start_as_current_span(f"chat {llm.model}") as span:
            span.set_attribute("gen_ai.operation.name", "chat")
            span.set_attribute("gen_ai.request.model", llm.model)
            span.set_attribute("lab.tenant_id", req.tenant_id)
            t0 = time.perf_counter()
            out = await llm.complete(msgs, req.max_tokens)
            LLM_LATENCY.labels(llm.model).observe(time.perf_counter() - t0)
            span.set_attribute("gen_ai.response.model", out.model)
            span.set_attribute("gen_ai.usage.input_tokens", out.usage.prompt_tokens)
            span.set_attribute("gen_ai.usage.output_tokens", out.usage.completion_tokens)
        LLM_TOKENS.labels("input", out.model, req.tenant_id).inc(out.usage.prompt_tokens)
        LLM_TOKENS.labels("output", out.model, req.tenant_id).inc(out.usage.completion_tokens)
        return {
            "text": out.text,
            "model": out.model,
            "usage": {
                "input_tokens": out.usage.prompt_tokens,
                "output_tokens": out.usage.completion_tokens,
            },
        }

    @app.post("/v1/chat/stream")
    async def chat_stream(req: ChatRequest) -> StreamingResponse:
        REQUESTS.labels("/v1/chat/stream", req.tenant_id).inc()
        llm = app.state.llm
        msgs = [Message(m["role"], m["content"]) for m in req.messages]

        async def events() -> AsyncIterator[str]:
            async for chunk in llm.stream(msgs, req.max_tokens):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        # Healthy baseline: tell nginx not to buffer this SSE response.
        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


app = create_app()
