"""The /v1/models surface must stay OpenAI-shaped - clients parse it."""

from __future__ import annotations


def test_models_returns_openai_list_shape(client) -> None:
    body = client.get("/v1/models").json()
    assert body["object"] == "list"
    assert isinstance(body["data"], list)
    assert body["data"]


def test_every_model_entry_has_required_fields(client) -> None:
    for entry in client.get("/v1/models").json()["data"]:
        assert {"id", "object", "created", "owned_by"} <= set(entry)
        assert entry["object"] == "model"


def test_owned_by_reports_the_provider(client) -> None:
    assert client.get("/v1/models").json()["data"][0]["owned_by"] == "stub"
