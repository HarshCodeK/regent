# Session Context

> Read this file first. It is the cheap way back into the project after time away.
> Append-only, newest entry first, kept under ~150 lines.

## 1. What this is

Regent - the AI control plane. One OpenAI-compatible endpoint that decides which model
answers a request, meters what it cost, and records the decision. Repository scaffolded
2026-09-15; rewrite of an earlier prototype (`kay-kay`) with real history and real tests.

## 2. State of the world

- Version: `v0.0.1` (walking skeleton), released 2026-09-15
- Tests: 32 passing, offline, no credentials needed
- Lint: `ruff check` + `ruff format --check` clean
- Working now: `/healthz`, `/v1/models`, `/v1/chat/completions` (stub provider),
  `/v1/usage`, ledger with integer costs, provider seam, OpenAI-compatible responses
- Not built: auth, budgets, real adapters, task-class routing, eval, UI (see limitations.md)

## 3. Landmines

- PowerShell 5.1's `Set-Content -Encoding UTF8` writes a BOM and can leave CRLF endings.
  `tomllib` rejects a BOM in `pyproject.toml`. If Python/ruff suddenly complains about
  "Invalid statement at line 1", strip the BOM and normalize to LF.
- `stub` models are in the price table at 0 on purpose (they are local and free).
  `price_unknown` only appears for a model with no entry at all.
- Tests must use the `client` fixture (tmp_path DB). Never let a test write to `./.regent/`.
- The `regent` block in responses is additive on purpose - do not move fields out of it.

## 4. Next action (REQUIRED - one concrete step)

Day 2: implement `src/providers/groq.py` - an OpenAI-compatible adapter with one retry,
selected by `REGENT_DEFAULT_PROVIDER=groq`. Tests must run against a fake HTTP transport,
not the network, and must cover the retry path.

## 5. Open questions

- Should `task_class` routing also steer retrieval depth, or only model tier?
- Does the ledger need a `request_id` column to join gateway rows with application logs?

## 6. Session entries (newest first)

### 2026-09-15 - scaffold + walking skeleton
Did: repo created, provider protocol, stub provider, SQLite ledger with integer
micro-USD costs, chat/usage/health endpoints, 32 tests, CI config, ADRs, this file.
Learned: BOM from PowerShell broke `tomllib`; ruff also flagged CRLF and a quoted
annotation. Both are now handled by `.gitattributes` and the ruff config.
Next: Day 2 real provider adapter.
