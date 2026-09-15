"""The append-only usage ledger.

One row per call, written whether the call succeeded or failed. Costs are stored
as integer micro-USD (1_000_000 = $1.00) so no float ever touches a money path -
the same discipline as integer paise in payment code, for the same reason.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    key_id TEXT NOT NULL,
    requested_model TEXT NOT NULL,
    served_model TEXT NOT NULL,
    provider TEXT NOT NULL,
    tier TEXT NOT NULL,
    decision_reason TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL,
    cost_micro_usd INTEGER NOT NULL,
    status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_llm_calls_created_at ON llm_calls (created_at);
CREATE INDEX IF NOT EXISTS idx_llm_calls_key ON llm_calls (key_id);
CREATE INDEX IF NOT EXISTS idx_llm_calls_model ON llm_calls (served_model);
"""

# Price per 1M tokens in micro-USD: (provider, model) -> (input, output).
# Kept as integers so arithmetic stays exact; extend when a provider is added.
PRICES_MICRO_USD_PER_MTOKEN: dict[tuple[str, str], tuple[int, int]] = {
    ("stub", "stub-small"): (0, 0),
    ("stub", "stub-large"): (0, 0),
    ("groq", "llama-3.1-8b-instant"): (50_000, 80_000),
    ("groq", "llama-3.3-70b-versatile"): (590_000, 790_000),
}


def estimate_cost_micro_usd(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> int:
    """Exact integer cost. Unknown provider/model prices as 0 and is visible in
    the ledger as `price_unknown` on the decision, never silently guessed."""
    if prompt_tokens < 0 or completion_tokens < 0:
        raise ValueError("token counts cannot be negative")
    price_in, price_out = PRICES_MICRO_USD_PER_MTOKEN.get((provider, model), (0, 0))
    return (prompt_tokens * price_in + completion_tokens * price_out) // 1_000_000


def price_is_known(provider: str, model: str) -> bool:
    return (provider, model) in PRICES_MICRO_USD_PER_MTOKEN


class Ledger:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def record(
        self,
        *,
        key_id: str,
        requested_model: str,
        served_model: str,
        provider: str,
        tier: str,
        decision_reason: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        status: str = "ok",
        created_at: float | None = None,
    ) -> int:
        cost = estimate_cost_micro_usd(provider, served_model, prompt_tokens, completion_tokens)
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO llm_calls (created_at, key_id, requested_model, served_model,
                provider, tier, decision_reason, prompt_tokens, completion_tokens,
                latency_ms, cost_micro_usd, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    created_at if created_at is not None else time.time(),
                    key_id,
                    requested_model,
                    served_model,
                    provider,
                    tier,
                    decision_reason,
                    prompt_tokens,
                    completion_tokens,
                    latency_ms,
                    cost,
                    status,
                ),
            )
            return int(cur.lastrowid or 0)

    def usage_summary(self) -> dict:
        with self.connect() as conn:
            totals = conn.execute(
                """SELECT COUNT(*) AS calls,
                          COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                          COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                          COALESCE(SUM(cost_micro_usd), 0) AS cost_micro_usd
                   FROM llm_calls"""
            ).fetchone()
            by_model = conn.execute(
                """SELECT served_model, COUNT(*) AS calls,
                          COALESCE(SUM(cost_micro_usd), 0) AS cost_micro_usd
                   FROM llm_calls GROUP BY served_model ORDER BY calls DESC"""
            ).fetchall()
        return {
            "calls": totals["calls"],
            "prompt_tokens": totals["prompt_tokens"],
            "completion_tokens": totals["completion_tokens"],
            "cost_micro_usd": totals["cost_micro_usd"],
            "cost_usd": round(totals["cost_micro_usd"] / 1_000_000, 6),
            "by_model": [dict(row) for row in by_model],
        }
