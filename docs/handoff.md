# Handoff

## Thread 1: orientation and scaffold (2026-11-26)

**Done**
- Read plan.pdf (20 pages, image-only PDF) and posted the lab order, the key design decision (blind game-day mode), and the risks.
- Built the scaffold on branch `scaffold`:
  - `CLAUDE.md` with the rules, the game day and reveal workflow, the layout, and the `FAULT_<AREA>_<NAME>` convention.
  - `.claude/settings.json` denying Claude Code Read/Edit/Write on `.gameday/**`.
  - A FastAPI monolith (`api/`): `/healthz`, `/v1/chat`, `/v1/chat/stream` (SSE, sends `X-Accel-Buffering: no`), `/metrics`, and token-guarded `/chaos`.
  - `chaos/flags.py` with an empty registry, so no faults are enabled.
  - `gateway/llm_client.py`: a deterministic stub LLM with TTFT, inter-token latency, token counts and cost.
  - `docker-compose.yml`: api, nginx, pgvector, postgres-state, qdrant, otel-collector, phoenix, prometheus and grafana, all with pinned tags. `.gameday/faults.env` is an optional env_file.
  - `postmortems/TEMPLATE.md` and `postmortems/INDEX.md`, plus `.gitignore` covering `.gameday/`.

**Verified in the cloud thread:** `docker compose config` is valid, `ruff check` and `ruff format --check` pass, and `pytest` passes (25 tests).

**Not run here** (no Docker daemon, no GPU): `docker compose up`, nginx `-t`, otelcol `validate` and `promtool check config` (binary download was blocked), real OTLP export to Phoenix, Grafana provisioning, and any image pull.

**Pinned versions**
- Images: pgvector 0.8.7-pg17-bookworm, postgres 17.12-bookworm, qdrant v1.20.2, nginx 1.30.8-alpine, otelcol-contrib 0.166.0, phoenix version-22.1.0, prometheus v3.15.1, grafana 13.2.7, python 3.13.18-slim-bookworm.
- Python packages: see `pyproject.toml`.
- OTel: `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`, content capture off.

**Open**
- Run `docker compose up --build` on the laptop and confirm that traces reach Phoenix and that Prometheus scrapes `api` and `otel-collector`.
- The game-day selector script (`chaos/gameday.py`) doesn't exist yet.
- Step A suggestions not acted on yet: use a BEIR subset with qrels for the golden set; batch GPU labs (2 and 7) together; write a thin gateway of our own rather than use LiteLLM; express faults as config values and add decoy flags.
- Starlette warns that the TestClient prefers `httpx2`. This is harmless for now.

**Next step:** Lab 0 in a fresh thread. Add GenAI spans for retrieve, rerank, llm, tool and guard, per-tenant cost, and a golden set.
