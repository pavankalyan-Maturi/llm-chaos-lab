# Postmortem: <FAULT_ID>, <one-line symptom>

| Field | Value |
|---|---|
| Fault ID | `FAULT_<AREA>_<NAME>` |
| Lab | Lab N |
| Date | YYYY-MM-DD |
| Mode | blind game day / known fault |
| Time to diagnose | mm:ss (blind only) |
| Versions | git SHA, images, vLLM, OTel semconv opt-in, MCP revision, pgvector |

## Impact
Who or what was affected, how badly, for how long. Give a number: % of requests, tenants affected, recall drop, p95 delta, $ wasted.

## Detection signal
The first signal that showed the problem. Name the exact metric, span attribute or log line, and attach a trace or dashboard screenshot. Say whether an alert fired or a human noticed.

## Timeline
| Time (local) | Event |
|---|---|
| T+0 | Fault active / load started |
| | First symptom observed |
| | Hypothesis 1 (and why it was wrong) |
| | Component isolated |
| | Mechanism identified |
| | Fix applied |
| | Fix verified |

## Root cause
One paragraph that explains the mechanism, not just the trigger.

## Contributing factors
- What made it worse, slower to detect, or possible at all (missing metric, default config, absent test).

## Fix options and tradeoffs
| Option | Tradeoff (latency / cost / recall / complexity) | Chosen? |
|---|---|---|
| | | |

## Verification number
| Metric | Before fix | After fix | How measured (n, load profile, seed) |
|---|---|---|---|
| | | | |

## Prevention
- Alert added: (metric, threshold)
- Test added: (path)
- Guardrail or config change: (what)

## Sources and caveats
Mark any number taken from a secondary source or a blog as **unverified** unless it was reproduced here.
