# Limitations - what Regent does not do yet

Required reading before you draw conclusions from the README. Every line is a
commitment to a later day, not an oversight.

| Not built | Why it matters | Planned |
|---|---|---|
| **Authentication** | Any caller can send any `api_key` today; keys are not issued or stored | Day 3 |
| **Budget enforcement** | The ledger *records* cost but does not *stop* spend at a limit | Day 8 |
| **Real provider adapter** | Only `StubProvider` exists; no request has ever left this machine | Day 2 |
| **Task-class routing** | `task_class` is accepted and recorded but does not change the model yet | Day 5 |
| **Eval harness** | No measured claim about routing quality or saving exists yet | Day 6 |
| **UI / dashboard** | Terminal and API only | Day 7 |
| **Streaming** | `stream=true` is accepted in the schema but not implemented | Week 3 |
| **Caching** | Every call is a fresh completion | Week 4 |
| **Multi-tenancy** | One flat key space, no teams, no per-tenant quotas | Week 5 |
| **Concurrency under load** | SQLite single-writer; no load test has been run | Week 9 |

## Known design choices (not bugs)

1. **`stub` is a first-class provider.** It exists so the pipeline is testable and
   demoable offline. It is not a mock to be removed later.
2. **`price_unknown` is deliberate.** A missing price is surfaced, never estimated.
3. **The `regent` block in responses is additive.** Stock OpenAI clients ignore unknown
   fields, which is what keeps the wire format compatible.
4. **SQLite is a deliberate start.** Single-writer is fine for one node; the ledger API
   is narrow enough that Postgres is a swap, not a rewrite.
