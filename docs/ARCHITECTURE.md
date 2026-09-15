# Architecture

## The one idea

The application talks to Regent once. Regent decides which model answers, what the
call is allowed to cost, and writes down what happened. Everything else is detail.

## Request flow

```
POST /v1/chat/completions
   |
   |  src/app.py        parse + validate (pydantic)
   v
  route  ->  src/<router>.py      pick a tier and a model from the policy
   |           v0.0.1: single tier, but the DECISION is still recorded
   v
  complete -> src/providers.py    Provider protocol -> one adapter per vendor
   |           stub (offline, CI) | groq | openai-compatible | ...
   v
  account -> src/ledger.py        one append-only row per call, success OR failure
   |           integer micro-USD, indexed by time / key / model
   v
  respond -> OpenAI-compatible JSON + a `regent` block
```

## Modules

| Module | Responsibility | Must never do |
|---|---|---|
| `src/app.py` | HTTP surface, wiring, error mapping | contain routing or pricing logic |
| `src/models.py` | Request/response schemas | know about providers or SQLite |
| `src/providers.py` | One adapter per vendor behind one protocol | write to the ledger |
| `src/ledger.py` | Cost arithmetic + append-only storage | call a provider or the network |
| `src/config.py` | Environment -> Settings | carry a hard-coded secret |

## Invariants (break these and the design is wrong)

1. **One row per call.** Success and failure both write a row. An unaccounted call is a bug.
2. **Money is integer.** Costs are integer micro-USD (1_000_000 = $1.00). No float ever
   touches a money path - the same rule as integer paise in payment code.
3. **Unknown price is never guessed.** If `(provider, model)` is absent from the price
   table, cost is 0 and the decision is flagged `price_unknown`.
4. **The provider is a seam, not a branch.** Adding a vendor is one adapter + one config line.
5. **The gateway works offline.** `StubProvider` runs the full pipeline with no credential,
   which is why CI never needs a secret and why the repo is demoable in one command.

## Why these choices

See `docs/adr/` for one-page decisions: why SQLite before Postgres, why integer money,
why a provider protocol, why a stub provider ships first.
