# regent

> **One endpoint. Every call accounted for.**
> An LLM gateway that routes to providers, enforces budgets, and writes an append-only ledger of every decision. Integer micro-USD — no float on a money path.

[![ci](https://github.com/HarshCodeK/regent/actions/workflows/ci.yml/badge.svg)](https://github.com/HarshCodeK/regent/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![tests](https://img.shields.io/badge/tests-32%20passing-brightgreen)
![coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)
![license](https://img.shields.io/badge/license-MIT-lightgrey)
![tier](https://img.shields.io/badge/tier-F-E3B341)

---

## The problem

Three things go wrong the moment a product starts using LLMs:

1. **Every request goes to the biggest model.** A 12-word classification task burns reasoning-model money. Nobody chooses that; it is just the default.
2. **Nobody can answer "what did AI cost us, per team, per feature?"** Providers bill per account, not per feature.
3. **Switching providers means rewiring the application.** So teams stay stuck.

Regent is the layer that sits between your app and the providers and fixes all three.

---

## How it works

```
client (OpenAI SDK, any language)
      │  base_url = http://localhost:8000/v1
      ▼
┌────────────────── Regent ──────────────────┐
│  route  →  complete  →  ledger             │
│    │           │          │                │
│  policy     provider   SQLite              │
│  (tier)     adapter    (integer µ-USD)     │
└────────────────────────────────────────────┘
      │                       │
      ▼                       ▼
  stub (offline)        GET /v1/usage
  groq / openai / ...   (spend by key, model, day)
```

- **OpenAI wire format** — switch by changing `base_url` and `api_key`
- **Integer money** — costs stored as integer micro-USD, no float drift
- **Stub provider** — runs the full pipeline with zero credentials

---

## Quickstart

```bash
pip install -r requirements.txt
python -m uvicorn src.app:app --reload --port 8000
```

No API key needed — `REGENT_DEFAULT_PROVIDER=stub` answers locally and deterministically.

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="stub")
print(client.chat.completions.create(
    model="stub-small",
    messages=[{"role": "user", "content": "classify: invoice overdue"}],
).choices[0].message.content)
```

---

## Evidence

| Metric | Value | Reproduce |
|---|---|---|
| tests passing | 32 | `python -m pytest -q` |
| coverage on src | 99% | `python -m pytest --cov=src` |
| HTTP endpoints | 5 | `grep -c '@app.' src/app.py` |
| money path floats | 0 | `python -m pytest tests/test_ledger.py -q` |
| CI matrix | 3.10, 3.11, 3.12, 3.13 | `.github/workflows/ci.yml` |

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/v1/chat/completions` | OpenAI-compatible chat completion |
| GET | `/v1/models` | List available models |
| GET | `/v1/usage` | Spend by key, model, day |
| GET | `/healthz` | Liveness + active provider |
| POST | `/v1/reset` | Reset ledger (testing) |

---

## The trust boundary

**Money is integer arithmetic.** Costs are stored as `int` (micro-USD). Pydantic models reject `float` for cost fields. This is not a style choice — it is the invariant that prevents rounding drift in financial records.

---

## What this is NOT (yet)

- No auth — v0.0.1 accepts any key
- No budget enforcement — ledger records cost, doesn't stop spend
- No real provider adapter — StubProvider is offline-only
- No dashboard UI — the CLI is the interface for now

---

## Architecture

```
src/
├── app.py          # FastAPI HTTP surface (OpenAI-compatible)
├── ledger.py       # Append-only SQLite ledger with integer costs
├── providers.py    # Provider protocol + StubProvider
├── models.py       # Pydantic schemas
├── config.py       # Settings from env vars
└── __init__.py

tests/
├── test_health.py
├── test_ledger.py        # 8 tests — integer costs, append-only
├── test_models_endpoint.py
├── test_providers.py
└── test_chat_completions.py
```

---

## License

MIT
