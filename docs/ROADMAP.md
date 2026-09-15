# Roadmap - 10 weeks, one release per week

Rule for every release: **one measurable claim, published in the README with the exact
command that reproduces it.** UI work happens after the backend of that week works, never
before, and every release keeps CI green.

| Week | Release | Scope | Measured claim required |
|---|---|---|---|
| 1 (Days 1-10) | **v0.1.0 - MVP** | Real provider adapter, per-key auth, task-class routing, eval harness, minimal UI, budgets, Docker | Routing serves N% of eval requests with the cheap model at equal score, and the saving in USD per 1k calls |
| 2 (Days 1-10 done) | v0.1.1 | Harden: 30+ tests, coverage gate, deploy to one host, README quickstart verified from scratch on a clean clone | p95 gateway overhead per request |
| 3 | v0.2.0 | Streaming responses + error taxonomy + retry policy per provider | streamed vs buffered p95, retry success rate |
| 4 | v0.3.0 | Semantic cache (embedding-based) with a correctness guard | cache hit rate and $ saved per 1k calls |
| 5 | v0.4.0 | Multi-tenancy: tenants, keys API, per-tenant quotas | isolation proven by test; quota enforcement at the boundary |
| 6 | v0.5.0 | Agent mode: tool loop with hard step/latency/cost caps | steps per request distribution, cost cap enforced |
| 7 | v0.6.0 | Knowledge module: chunking + local embeddings + citation requirement | retrieval hit rate on a labelled question set |
| 8 | v0.7.0 | Offline degradation: circuit breaker, RAG-only answers, auto-resume | time-to-degrade and answer-quality delta offline vs online |
| 9 | v0.8.0 | Observability: request ids, structured logs, `/metrics`, load test | measured p50/p95/p99 under load; where the first bottleneck is |
| 10 | **v1.0.0** | Cost-governance report + Next.js dashboard + public demo | "X% of spend went to tasks a small model passed" - with the eval to prove it |

## Discipline that makes this real

- One feature per branch and PR, even solo; squash-merge, conventional commit messages.
- Tag every release; write the GitHub Release with the measured delta.
- Weekly, not daily, is fine - but never let a week pass with zero commits.
- If a week's claim cannot be measured, the release is not done.
