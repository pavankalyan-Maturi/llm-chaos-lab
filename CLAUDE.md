# LLM Chaos Lab: rules for Claude Code

This repo is a fault-injection lab for production LLM systems (RAG, agents, MCP,
gateway, guardrails, serving, evals). Its owner breaks the system on purpose,
diagnoses the failure from traces and metrics, fixes it, and proves the fix
with a number. The source of truth for the plan is `plan.pdf` in the project
files, not this repo.

## Hard rules

1. **Never fix a bug unless the owner says "fix it".** When a symptom comes up,
   do not name the root cause first. Ask which signal they would check first,
   then hint in escalating order: **signal, then component, then mechanism**.
   Give the answer only when they say **"reveal"**.
2. **No commits, branches or PRs unless the owner says "build" or "fix it".**
   Never merge.
3. **Every fix ends with a number and a postmortem.** The number is measured
   before and after the fix (recall@k, TTFT p95, cache hit rate, false-positive
   rate, cost per request, attack success rate). The postmortem uses
   `postmortems/TEMPLATE.md` and gets a row in `postmortems/INDEX.md`.
4. **Pin every version.** That means Docker image tags (never `latest`), Python
   packages (`==` in `pyproject.toml`), vLLM, the OTel GenAI semconv opt-in, MCP
   revision `2026-07-28`, and pgvector. Write the pinned versions into every
   postmortem.
5. **Be honest about sources.** Mark anything that comes from a secondary
   source or a single-engineer blog as unverified. It must be reproduced here
   before anyone quotes it.
6. **Keep threads short.** Each thread ends by updating `docs/handoff.md` with
   what was done, what's open, and the next step.

## Game day and reveal workflow

- **"game day"** means a blind run. A selector script picks a random subset of
  `FAULT_*` flags plus a load profile. It writes the active flags to
  `.gameday/faults.env` and the answer key to `.gameday/answer.md`. Both are
  gitignored.
- **Never read, cat, grep, summarize or hint at anything in `.gameday/`.** The
  deny rule in `.claude/settings.json` enforces this. Don't try to work around
  it, for example by printing env vars from the running containers, calling
  `GET /chaos` during a blind run, or reading process environments.
- During a game day, diagnose only from dashboards, traces, metrics and logs
  (Phoenix, Grafana, Prometheus, container logs).
- **"reveal"** means the owner compares their diagnosis with
  `.gameday/answer.md` themselves. Only after that may Claude discuss the root
  cause.
- Log time-to-diagnose in blind mode in `postmortems/INDEX.md`.

## Layout

| Dir | Holds |
|---|---|
| `api/` | FastAPI app (the monolith entry point), `/chaos` admin endpoint, telemetry setup |
| `gateway/` | LLM client(s), routing, retries, rate limits, exact and semantic cache, SSE |
| `ingest/` | Parsing, chunking, embedding, versioned indexes |
| `agent/` | Planner/executor loop, budgets, state checkpoints (Postgres) |
| `mcp_servers/` | MCP servers (Streamable HTTP, revision 2026-07-28): benign tools, `create_ticket`, a "malicious" server |
| `guards/` | Input/output classifiers, CaMeL-lite structural defense |
| `serving/` | vLLM launch configs for rented GPUs (RunPod / Modal). Never run vLLM locally |
| `evals/` | Golden set, judges, CI gate |
| `chaos/` | Fault-flag registry, game-day selector, load profiles |
| `postmortems/` | One SRE postmortem per fault, plus `INDEX.md` |
| `infra/` | nginx, OTel collector, Prometheus, Grafana and Postgres configs used by `docker-compose.yml` |
| `docs/` | `handoff.md` and replication notes |

## Fault-flag convention

- Every fault is a flag named **`FAULT_<AREA>_<NAME>`**, upper snake case. AREA
  is one of `INGEST`, `RETRIEVAL`, `GATEWAY`, `AGENT`, `MCP`, `GUARD`,
  `SERVING`, `EVAL`, `OBS`, `DEPLOY`. Example: `FAULT_RETRIEVAL_HNSW_POSTFILTER`.
- Register every flag in `chaos/flags.py` (`REGISTRY`) with its area, a
  one-line neutral description, and its default value. The description must
  not give away the mechanism, because the registry is readable.
- Read flags only through `chaos.flags.is_enabled()` / `chaos.flags.value()`,
  never `os.environ` directly.
- Flags come from the environment at startup and can be overridden at runtime
  through the **`/chaos` admin endpoint** (`GET /chaos`, `POST /chaos`,
  `DELETE /chaos`), which requires the `X-Chaos-Token` header. All faults
  default to off.
- Prefer faults that change a **config value** (ef_search, thresholds, a
  header, a timeout) over obvious `if fault:` branches. They are more realistic
  and harder to spot by reading the code.

## Verification in cloud threads

Cloud threads have no Docker daemon, GPU or RunPod. In them, run only
`docker compose config`, `ruff check .`, and `pytest`. Say plainly what could
not be run.
