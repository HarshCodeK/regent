"""Request and response schemas.

The request/response shapes are OpenAI-compatible so existing clients work
unchanged. Regent-specific fields are additive and namespaced under `regent`
in the response, so an OpenAI SDK never breaks on them.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float = 0.0
    max_tokens: int | None = None
    stream: bool = False
    # Regent extension: what the work IS, decoupled from which model serves it.
    task_class: str | None = None


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage
    regent: dict[str, Any] = Field(default_factory=dict)
