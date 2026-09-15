# ADR 0001 - SQLite for the usage ledger

**Status:** accepted (2026-09-15)
**Deciders:** Harsh Paresh Kharavle

## Context

Every LLM call must be recorded with tokens, latency and cost, and the record must be
queryable for spend-by-key / spend-by-model / spend-by-day. Expected early volume is a
few thousand rows. The project runs on one machine and must start with zero
infrastructure so that a reviewer can clone and run it in one command.

## Options considered

| Option | Why not (yet) |
|---|---|
| Postgres | Needs a server or a hosted dependency; fails the "clone and run" test |
| JSONL append-only file | No indexing, no aggregation, painful concurrent reads |
| **SQLite** | Single-writer, but zero setup, real indexes, one file to back up |

## Decision

Use SQLite with explicit schema creation and indexes on `created_at`, `key_id`, `served_model`.
Keep all access behind the narrow `Ledger` API (`record`, `usage_summary`) so the storage
engine is replaceable.

## Consequences

- Positive: zero setup, real SQL aggregation, easy testing against a `tmp_path` file,
  the whole ledger is one file to copy.
- Positive: money arithmetic stays integer and is unit-tested independently of storage.
- Negative: single-writer. Concurrent writers need a queue or WAL tuning.
- Negative: no multi-node aggregation. Revisit in Week 5 (multi-tenancy) or Week 9 (load).
- Triggers for revisiting: sustained write contention, >10M rows, or a second gateway node.
