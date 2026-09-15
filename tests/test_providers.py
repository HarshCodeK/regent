"""Provider seam: the gateway must stay independent of any single provider."""

from __future__ import annotations

import pytest

from src.providers import StubProvider, rough_tokens


def test_stub_is_deterministic() -> None:
    provider = StubProvider()
    args = ("stub-small", [{"role": "user", "content": "same input"}])
    assert provider.complete(*args) == provider.complete(*args)


def test_stub_echoes_the_last_user_message() -> None:
    out = StubProvider().complete("stub-small", [{"role": "user", "content": "hello world"}])
    assert "hello world" in out.text
    assert out.text.startswith("[stub-small]")


def test_prompt_tokens_sum_every_message() -> None:
    messages = [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "one two three"},
    ]
    out = StubProvider().complete("stub-small", messages)
    assert out.prompt_tokens == sum(rough_tokens(m["content"]) for m in messages)


def test_unknown_model_raises_so_the_caller_can_log_it() -> None:
    with pytest.raises(ValueError):
        StubProvider().complete("nope", [{"role": "user", "content": "x"}])


def test_advertised_models_match_what_it_serves() -> None:
    provider = StubProvider()
    assert provider.models == ("stub-small", "stub-large")


def test_empty_text_still_counts_one_token() -> None:
    assert rough_tokens("") == 1
