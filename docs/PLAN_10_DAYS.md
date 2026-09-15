# 10-day plan - MVP first, UI in between

Rule for all ten days: **the MVP is finished before any UI work starts.** UI days are
earned, not scheduled first. Every day ends with a green gate and one commit:

```
python -m ruff check . && python -m ruff format --check . && python -m pytest -q
```

Budget: 2-3 h/day. If a day overruns, cut scope inside the day (fewer endpoints,
fewer tests) - never carry a broken gate into the next day.

---

## Phase A - the MVP (Days 1-6)

### Day 1 - scaffold + walking skeleton  **DONE 2026-09-15**

- Goal: the pipeline exists end to end and can be demoed offline.
- Built: provider protocol + `StubProvider`, SQLite ledger with integer micro-USD costs,
  `/healthz`, `/v1/models`, `/v1/chat/completions`, `/v1/usage`, CI config, LICENSE,
  ADR-0001, this plan.
- Evidence: 32 tests passing, `ruff check` + `ruff format --check` clean, live uvicorn
  smoke test returned an OpenAI-shaped completion and wrote 1 ledger row.
- Commit: `chore: scaffold repository` ... `docs: ...` (7 commits, see git log)

### Day 2 - real provider adapter

- Build: `src/providers/groq.py` (OpenAI-compatible over HTTP), selected by
  `REGENT_DEFAULT_PROVIDER=groq`. One retry on 5xx/timeout, then a typed provider error.
- Tests: fake HTTP transport, not the network. Cover success, retry-then-success,
  retry-then-fail, malformed JSON, and that a failed call still writes `status="error"`.
- Own it: `groq.py` must be in `OWNERSHIP.md` as `owned` by end of day.
- Done when: with a real key set, one live request appears in `/v1/usage` with real tokens.
- Commit: `feat(providers): groq adapter with one retry`

### Day 3 - keys and auth

- Build: `regent_keys` table (SHA-256 hash only, never the raw key), admin bootstrap key,
  bearer auth middleware, 401 paths, `POST /v1/keys` (admin only), key id on every ledger row.
- Tests: valid key, missing header, wrong key, revoked key, hash-not-plaintext assertion,
  admin-only enforcement.
- Done when: `curl` without a key returns 401 and the ledger shows the key id (not the key).
- Commit: `feat(auth): hashed keys and bearer auth`

### Day 4 - the eval harness (the part that makes claims possible)

- Build: `eval/dataset.jsonl` (~60 labelled examples: classification / extraction /
  reasoning), `eval/run.py` that scores a model against the labels and prints a table.
- Tests: scoring math is unit-tested on a fixed fixture with known answers.
- Done when: `python -m eval.run` prints accuracy per task class, reproducibly.
- Commit: `feat(eval): labelled task set and scoring harness`

### Day 5 - task-class routing

- Build: `routing.yaml` policy (task class -> tier -> model), `src/router.py` returning
  `(model, tier, reason)`, wired into the endpoint. `task_class` now actually changes the model.
- Tests: each class maps to the expected model; unknown class falls back safely and is
  flagged; explicit `model` in the request still wins.
- Done when: one request with `task_class=classification` is served by the cheap model,
  and the ledger `decision_reason` explains why.
- Commit: `feat(routing): task-class policy picks the model tier`

### Day 6 - MVP complete: publish the measured claim

- Build: run the eval twice (cheap tier vs strong tier), record both, compute the saving in
  USD per 1k calls, and put the numbers in the README table with the reproducing command.
- Also: `docs/QA.md` questions 2, 3, 7, 9 answered with these numbers.
- Done when: the README says something like *"the cheap tier scored X% vs Y% at 1/N cost,
  so N% of requests are served cheaper at equal quality"* - and a reviewer can rerun it.
- Commit: `docs: publish v0.1.0 measured routing result` + tag `v0.1.0`

**MVP definition of done:** auth, real provider, routing, ledger with real costs, eval
harness with published numbers, 40+ tests, CI green. No UI required for this to be true.

---

## Phase B - UI and operations (Days 7-10)

### Day 7 - dashboard v1 (first UI element)

- Build: Streamlit page over `/v1/usage`: spend by day, spend by model, call counts,
  routing-decision breakdown, top keys. Read-only - no writes, no auth bypass.
- Tests: the query helpers behind the page are unit-tested; the page itself is smoke-tested.
- Done when: someone else can open it and understand where money went in 10 seconds.
- Commit: `feat(ui): usage and routing dashboard`

### Day 8 - budgets and rate limits

- Build: per-key monthly budget, spend check before the call, 402/429 responses,
  simple token-bucket rate limit, and a `budget_exceeded` decision reason in the ledger.
- Tests: under budget, exactly at budget, over budget, refill/burst edge cases.
- Done when: a key with a 1-rupee budget is refused after exceeding it - proven by a test.
- Commit: `feat(budget): per-key budget and rate limiting`

### Day 9 - package and deploy it

- Build: `Dockerfile` + `docker-compose.yml`, `/metrics` (Prometheus text), structured JSON
  logs with request ids, and a real deploy to one cheap host with a public URL.
- Tests: container smoke test hit with curl; `/metrics` shape asserted.
- Done when: the README quickstart works on a clean clone, and a public URL answers `/healthz`.
- Commit: `feat(ops): docker, metrics, structured logs, public deploy`

### Day 10 - harden and release v0.1.1

- Build: raise to 50+ tests, coverage gate at 80%, PR + issue templates, `SECURITY.md`,
  `docs/RUNBOOK.md` (how to debug, how to roll back), load test with `hey`/`ab`,
  README polish pass, GitHub Release notes, pin the repo on the profile.
- Done when: a stranger can clone, run, and reproduce every number in the README in under
  10 minutes, and the release notes list what changed and what was measured.
- Commit: `docs: v0.1.1 release notes` + tag `v0.1.1`

---

## What continues after Day 10

Weekly cadence from `docs/ROADMAP.md` (weeks 3-10), one release and one measured claim per
week, UI at the end of each week - never before the backend of that week.

## Anti-drift rules

1. The gate runs before every commit. A red gate means no commit, not a `--no-verify`.
2. One day = one feature = one commit (or a small PR). Never a single dump at the end.
3. Every session ends by appending to `docs/SESSION_CONTEXT.md` (what I did, what I
   learned, next action). This is what makes re-entry cheap.
4. Any claim that cannot be reproduced by a command stays out of the README.
