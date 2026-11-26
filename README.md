# llm-chaos-lab

A fault-flag monolith for practicing production debugging of LLM systems: break it on purpose, diagnose from traces and metrics, fix it, and prove the fix with a number. Rules for working in this repo are in [CLAUDE.md](CLAUDE.md).

## Run locally (needs Docker)

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| API through nginx | http://localhost:8080 |
| Phoenix (traces) | http://localhost:6006 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

Smoke test:

```bash
curl -s localhost:8080/v1/chat -H 'content-type: application/json' \
  -d '{"tenant_id":"t1","messages":[{"role":"user","content":"hi"}]}'
curl -N localhost:8080/v1/chat/stream -H 'content-type: application/json' \
  -d '{"tenant_id":"t1","messages":[{"role":"user","content":"hi"}]}'
```

## Tests

```bash
pip install -e '.[dev]'
ruff check . && pytest
```

No faults are registered yet. See `chaos/flags.py` and the fault-flag convention in CLAUDE.md.
