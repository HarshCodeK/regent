"""Service card and liveness."""

from __future__ import annotations


def test_service_card_names_the_endpoints(client) -> None:
    body = client.get("/").json()
    assert body["name"] == "regent"
    assert "/v1/chat/completions" in body["endpoints"]


def test_service_card_admits_what_is_not_built(client) -> None:
    not_built = client.get("/").json()["not_built_yet"]
    assert "auth" in not_built


def test_healthz_reports_provider_and_models(client) -> None:
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert body["provider"] == "stub"
    assert "stub-small" in body["models"]
