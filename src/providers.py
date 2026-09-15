"""Provider adapters.

The gateway only ever talks to this interface. That single seam is why a new
provider is an adapter plus a config line, and never a change to routing, budget
or ledger code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Completion:
    text: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str = "stop"


def rough_tokens(text: str) -> int:
    """Deliberately crude and deterministic token estimate for offline mode."""
    return max(1, len(text.split()))


class Provider(Protocol):
    name: str
    models: tuple[str, ...]

    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> Completion: ...


class StubProvider:
    """Offline provider: no network, no credential, deterministic output.

    It exists so route -> complete -> ledger is testable and demoable with zero
    setup, and so CI never depends on a third party being reachable.
    """

    name = "stub"
    models = ("stub-small", "stub-large")

    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> Completion:
        if model not in self.models:
            raise ValueError(f"unknown stub model: {model}")
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        text = f"[{model}] {last_user}".strip()
        return Completion(
            text=text,
            prompt_tokens=sum(rough_tokens(m["content"]) for m in messages),
            completion_tokens=rough_tokens(text),
        )
