"""Ledger: money is integer arithmetic, and the failure path is logged too."""

from __future__ import annotations

import pytest

from src.ledger import Ledger, estimate_cost_micro_usd, price_is_known


def test_cost_is_exact_for_a_million_input_tokens() -> None:
    # 1M input tokens of llama-3.1-8b-instant at $0.05/1M = 50_000 micro-USD.
    assert estimate_cost_micro_usd("groq", "llama-3.1-8b-instant", 1_000_000, 0) == 50_000


def test_cost_adds_input_and_output_prices() -> None:
    price_in, price_out = 50_000, 80_000
    assert (
        estimate_cost_micro_usd("groq", "llama-3.1-8b-instant", 1_000_000, 1_000_000)
        == price_in + price_out
    )


def test_unknown_model_prices_as_zero_and_is_reported_unknown() -> None:
    assert estimate_cost_micro_usd("groq", "mystery-model", 10_000, 10_000) == 0
    assert price_is_known("groq", "mystery-model") is False


def test_known_model_is_reported_known() -> None:
    assert price_is_known("groq", "llama-3.3-70b-versatile") is True


def test_negative_tokens_are_rejected() -> None:
    with pytest.raises(ValueError):
        estimate_cost_micro_usd("groq", "llama-3.1-8b-instant", -1, 0)


def test_init_creates_schema_and_indices(tmp_path) -> None:
    led = Ledger(tmp_path / "nested" / "regent.db")
    led.init()
    with led.connect() as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        indices = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert "llm_calls" in tables
    assert {"idx_llm_calls_created_at", "idx_llm_calls_key", "idx_llm_calls_model"} <= indices


def test_record_returns_row_id_and_usage_aggregates(tmp_path) -> None:
    led = Ledger(tmp_path / "regent.db")
    led.init()
    first = led.record(
        key_id="k1",
        requested_model="m",
        served_model="stub-small",
        provider="stub",
        tier="default",
        decision_reason="single_tier_mvp",
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=12,
    )
    led.record(
        key_id="k1",
        requested_model="m",
        served_model="stub-large",
        provider="stub",
        tier="default",
        decision_reason="single_tier_mvp",
        prompt_tokens=20,
        completion_tokens=10,
        latency_ms=7,
    )
    summary = led.usage_summary()
    assert first == 1
    assert summary["calls"] == 2
    assert summary["prompt_tokens"] == 30
    assert summary["completion_tokens"] == 15
    assert len(summary["by_model"]) == 2


def test_error_rows_are_recorded_with_status(tmp_path) -> None:
    led = Ledger(tmp_path / "regent.db")
    led.init()
    led.record(
        key_id="k1",
        requested_model="m",
        served_model="stub-small",
        provider="stub",
        tier="default",
        decision_reason="single_tier_mvp;error",
        prompt_tokens=0,
        completion_tokens=0,
        latency_ms=3,
        status="error",
    )
    with led.connect() as conn:
        row = conn.execute("SELECT status, cost_micro_usd FROM llm_calls").fetchone()
    assert row["status"] == "error"
    assert row["cost_micro_usd"] == 0
