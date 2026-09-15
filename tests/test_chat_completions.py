"""Chat completions: wire compatibility plus the accounting guarantee."""

from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from src import app as app_module
from src.providers import Completion


def _post(client, **overrides):
    payload = {"messages": [{"role": "user", "content": "classify this charge"}]}
    payload.update(overrides)
    return client.post("/v1/chat/completions", json=payload)


class _UnpricedProvider:
    """Serves a model that has no entry in the price table - the case that must
    be flagged rather than silently costed at zero."""

    name = "fake"
    models = ("fake-unpriced",)

    def complete(self, model, messages, temperature=0.0, max_tokens=None) -> Completion:
        return Completion(text="ok", prompt_tokens=3, completion_tokens=1)


def test_returns_openai_compatible_shape(client) -> None:
    body = _post(client).json()
    assert body["id"].startswith("chatcmpl-")
    assert body["object"] == "chat.completion"
    assert isinstance(body["created"], int)
    assert body["choices"][0]["message"]["role"] == "assistant"


def test_usage_totals_add_up(client) -> None:
    usage = _post(client, model="stub-large").json()["usage"]
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
    assert usage["prompt_tokens"] > 0


def test_requested_model_is_the_served_model(client) -> None:
    assert _post(client, model="stub-large").json()["model"] == "stub-large"


def test_default_model_used_when_model_omitted(client) -> None:
    assert _post(client).json()["model"] == "stub-small"


def test_response_carries_the_routing_decision(client) -> None:
    regent = _post(client, task_class="classification").json()["regent"]
    assert regent["decision_reason"] == "single_tier_mvp"
    assert regent["task_class"] == "classification"
    assert regent["provider"] == "stub"


def test_priced_model_is_not_flagged_as_unknown_price(client) -> None:
    regent = _post(client, model="stub-large").json()["regent"]
    assert "price_unknown" not in regent["decision_reason"]


def test_unpriced_served_model_is_flagged_end_to_end(client, settings, monkeypatch) -> None:
    monkeypatch.setitem(app_module.PROVIDERS, _UnpricedProvider.name, _UnpricedProvider())
    cfg = replace(settings, default_provider="fake", default_model="fake-unpriced")
    with TestClient(app_module.create_app(cfg)) as fake_client:
        regent = _post(fake_client).json()["regent"]
    assert "price_unknown" in regent["decision_reason"]
    assert regent["cost_micro_usd"] == 0


def test_every_call_writes_exactly_one_ledger_row(client) -> None:
    before = client.get("/v1/usage").json()["calls"]
    _post(client)
    _post(client)
    assert client.get("/v1/usage").json()["calls"] == before + 2


def test_ledger_row_records_decision_and_latency(client) -> None:
    _post(client)
    summary = client.get("/v1/usage").json()
    assert summary["by_model"][0]["served_model"] == "stub-small"
    assert summary["by_model"][0]["calls"] == 1


def test_empty_messages_are_rejected(client) -> None:
    assert _post(client, messages=[]).status_code == 422


def test_invalid_role_is_rejected(client) -> None:
    resp = _post(client, messages=[{"role": "wizard", "content": "hi"}])
    assert resp.status_code == 422


def test_unknown_stub_model_surfaces_as_provider_error_and_is_still_logged(client) -> None:
    resp = _post(client, model="does-not-exist")
    assert resp.status_code == 502
    summary = client.get("/v1/usage").json()
    assert summary["calls"] == 1
