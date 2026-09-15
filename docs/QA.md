# QA - the twelve questions

Answered in writing, without the AI, after each module or release. An unanswered
question is not a failure; pretending it is answered is. Re-answer after every release.

Answer status: `answered` | `partial` | `unknown` (with the day it will be answered)

| # | Question | Status | Answer |
|---|---|---|---|
| 1 | Why this design and not the obvious alternative? | partial | One endpoint + one provider seam means a new vendor is an adapter, not a rewrite. Alternative (per-provider branches in handlers) fails invariant 4 in ARCHITECTURE.md. |
| 2 | What breaks first at 10x? | unknown | Suspected: SQLite single-writer under concurrent requests. Measure on Day 9 / Week 9. |
| 3 | What did you measure, on what data, which command? | unknown | Nothing measured yet by design; README table fills at v0.1.0 with `python -m eval.run`. |
| 4 | Worst bug shipped here, and how was it found? | unknown | Candidate already: a BOM in `pyproject.toml` broke the test runner. Found by running the gate. |
| 5 | What would you delete to cut half? | partial | The stub provider is the one piece visitors mistake for a mock, but it is what keeps CI credential-free - keep it, delete the `/` service card instead. |
| 6 | How do you know the LLM part cannot cause an unsafe action? | partial | v0.0.1 has no tool calls and no money path at all, so the answer is trivially yes - and it must stay that way when agent mode arrives (Week 6). |
| 7 | What does this cost per request, and how was it computed? | partial | Integer micro-USD from the price table; `estimate_cost_micro_usd` is unit-tested. Real-provider numbers do not exist yet. |
| 8 | What fails silently? | unknown | Unknown: provider errors are mapped to 502 and logged, but nothing detects a wrong-but-successful answer yet. This is the honest weak point. |
| 9 | p95 latency, and how was it measured? | unknown | Refresh: local p50/p95 not yet measured; `latency_ms` is recorded per call, so the data exists. |
| 10 | Show me a failing test and the bug it caught. | not yet | The price-flag test was wrong on first write (`stub-large` is priced) - see session entry 2026-09-15. |
| 11 | What did you try that did not work? | answered | Asserting `price_unknown` for a priced stub model. Replaced with an unpriced fake provider, which tests the real rule. |
| 12 | What is next, and why that first? | answered | Day 2 real adapter - because an unmetered gateway has never seen a real token count. |
