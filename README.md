# Regent

> **The AI control plane.** Your application talks to Regent once. Regent decides
> which model answers, enforces what you are allowed to spend, and records what
> every answer cost. Model-agnostic by design; OpenAI-compatible on the wire.
>
> _We do not build AI. We decide how a company's software should use AI._

[![ci](https://github.com/HarshCodeK/regent/actions/workflows/ci.yml/badge.svg)](https://github.com/HarshCodeK/regent/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

**Status: v0.0.1 - walking skeleton.** The pipeline is end to end and offline-runnable
(stub provider, no API key needed), but most features below are not built yet.
Everything not built is listed under [What this is NOT](#what-this-is-not) and in
[docs/limitations.md](docs/limitations.md). Nothing here is claimed before it is measured.

---

## The problem

Three things go wrong the moment a product starts using LLMs in production:

1. **Every request goes to the biggest model.** A 12-word classification task burns
   reasoning-model money. Nobody chooses that; it is just the default.
2. **Nobody can answer "what did AI cost us, per team, per feature?"** Providers bill
   per account, not per feature, and the app logs do not carry the price.
3. **Switching or adding a provider means rewiring the application.** So teams stay
   stuck with whatever they integrated first.

The result is a system nobody can budget, audit or migrate. Regent is the layer that
sits between the application and the providers and fixes all three.

## What exists today (v0.0.1)

- `POST /v1/chat/completions` - OpenAI wire format, so an existing app switches by
  changing `base_url` and `api_key`
- `GET /v1/models` - OpenAI-shaped model list
- `GET /healthz` - liveness plus the active provider and its models
- **Ledger** - every call is written to SQLite with provider, requested model, served
  model, tokens in/out, latency, cost and the routing decision that produced it
- **Integer money** - costs are stored as integer micro-USD so no float touches a
  money path
- **Offline provider** - `StubProvider` runs the full pipeline with zero credentials,
  which is also what CI tests against

```
client (OpenAI SDK, any language)
      |  base_url = http://localhost:8000/v1
      v
+---------------------- Regent ----------------------+
|  route  ->  complete  ->  ledger                   |
|    |           |            |                      |
|  policy     provider     SQLite (integer          |
|  (tier)     adapter      micro-USD costs)          |
+----------------------------------------------------+
      |                         |
      v                         v
  stub (offline)          GET /v1/usage
  groq / openai / ...     (spend by key, model, day)
```

## Quickstart

```bash
pip install -r requirements-dev.txt
python -m uvicorn src.app:app --reload --port 8000
```

No API key is required: with `REGENT_DEFAULT_PROVIDER=stub` the gateway answers
locally and deterministically.

```bash
curl -s http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"classify: invoice overdue\"}],\"task_class\":\"classification\"}"
```

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-used-in-stub-mode")
print(client.chat.completions.create(
    model="stub-small",
    messages=[{"role": "user", "content": "hello"}],
).choices[0].message.content)
```

Run the tests and the linter exactly as CI does:

```bash
python -m ruff check . && python -m ruff format --check .
python -m pytest -q
```

## Measured results

| Metric | Value | How to reproduce |
|---|---|---|
| Tests | see CI badge (pytest count is printed) | `python -m pytest -q` |
| Cost saving from task-class routing | _filled at v0.1.0 (Day 6)_ | `python -m eval.run` |
| p95 gateway overhead added per request | _filled at v0.1.0_ | `python -m eval.latency` |

This table is intentionally empty until the numbers exist. A claim without a
reproducing command does not go in this README.

## What this is NOT

- **No auth yet.** v0.0.1 accepts any key; per-key issuance and hashed storage land
  on Day 3.
- **No budget enforcement yet.** The ledger *records* cost; it does not yet *stop*
  spend. That is Day 8.
- **No real provider adapter yet.** `StubProvider` is offline-only; the Groq /
  OpenAI-compatible adapter lands on Day 2.
- **No UI yet.** The dashboard is Day 7, after the MVP works.
- **No streaming, no caching, no multi-tenancy.** See [docs/ROADMAP.md](docs/ROADMAP.md).

The full honest list lives in [docs/limitations.md](docs/limitations.md).

## Roadmap

10 weeks, one release per week, each release carrying one measured claim:
[v0.1.0 MVP on Day 10, v1.0.0 on week 10](docs/ROADMAP.md).
Day-by-day execution plan: [docs/PLAN_10_DAYS.md](docs/PLAN_10_DAYS.md).

## Design decisions

Irreversible choices are recorded as one-page ADRs in [docs/adr/](docs/adr):
SQLite for the ledger, integer micro-USD for money, a provider protocol instead of
per-provider branching, and "stub provider first" so CI never needs a credential.

## How this was built

This project is built with AI assistance and that is not hidden: the rule is that
**every module in `src/` is owned** - written by hand, or generated and then rewritten
until the author can defend every line. [docs/OWNERSHIP.md](docs/OWNERSHIP.md) tracks
that per module, and [docs/QA.md](docs/QA.md) holds the twelve questions the author
must be able to answer cold before a module counts as owned.

## License

MIT - see [LICENSE](LICENSE).
