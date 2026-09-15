"""Regent's HTTP surface.

OpenAI-compatible on the wire: an existing application switches to Regent by
changing `base_url` and `api_key`. Everything Regent adds is additive and
namespaced under `regent` in the response, so a stock OpenAI SDK parses our
responses without modification.
"""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from . import __version__
from .config import Settings
from .ledger import Ledger, estimate_cost_micro_usd, price_is_known
from .models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Usage,
)
from .providers import Provider, StubProvider

PROVIDERS: dict[str, Provider] = {StubProvider.name: StubProvider()}


def resolve_provider(settings: Settings) -> Provider:
    provider = PROVIDERS.get(settings.default_provider)
    if provider is None:
        raise RuntimeError(
            f"unknown provider {settings.default_provider!r}; available: {sorted(PROVIDERS)}"
        )
    return provider


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or Settings.from_env()
    provider = resolve_provider(cfg)
    ledger = Ledger(cfg.db_path)
    ledger.init()

    app = FastAPI(
        title="Regent",
        version=__version__,
        description="The AI control plane: route, meter and account for every LLM call.",
    )
    app.state.settings = cfg
    app.state.provider = provider
    app.state.ledger = ledger

    # Static dashboard
    _public = Path(__file__).resolve().parent.parent / "public"
    app.mount("/assets", StaticFiles(directory=str(_public / "assets")), name="assets")

    @app.get("/")
    def service_card() -> dict:
        return {
            "name": "regent",
            "version": __version__,
            "status": "walking-skeleton",
            "provider": provider.name,
            "endpoints": ["/healthz", "/v1/models", "/v1/chat/completions", "/v1/usage"],
            "not_built_yet": [
                "auth",
                "budget enforcement",
                "real provider adapters",
                "dashboard",
            ],
        }

    @app.get("/healthz")
    def healthz() -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "provider": provider.name,
            "models": list(provider.models),
        }

    @app.get("/v1/models")
    def list_models() -> dict:
        now = int(time.time())
        return {
            "object": "list",
            "data": [
                {"id": model, "object": "model", "created": now, "owned_by": provider.name}
                for model in provider.models
            ],
        }

    @app.get("/v1/usage")
    def usage() -> dict:
        return app.state.ledger.usage_summary()

    @app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
    def chat_completions(request: Request, body: ChatCompletionRequest) -> ChatCompletionResponse:
        led: Ledger = request.app.state.ledger
        prov: Provider = request.app.state.provider

        # v0.0.1 routing: one tier. The decision is still recorded, so the ledger
        # has the same shape it will have once task-class routing lands (Day 5).
        served_model = body.model or cfg.default_model
        tier = "default"
        reason = "single_tier_mvp"
        if not price_is_known(prov.name, served_model):
            reason = f"{reason};price_unknown"

        started = time.perf_counter()
        messages = [m.model_dump() for m in body.messages]
        try:
            completion = prov.complete(
                model=served_model,
                messages=messages,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            )
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            led.record(
                key_id="anonymous",
                requested_model=body.model or cfg.default_model,
                served_model=served_model,
                provider=prov.name,
                tier=tier,
                decision_reason=f"{reason};error",
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=latency_ms,
                status="error",
            )
            raise HTTPException(status_code=502, detail=f"provider error: {exc}") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_micro_usd = estimate_cost_micro_usd(
            prov.name, served_model, completion.prompt_tokens, completion.completion_tokens
        )
        led.record(
            key_id="anonymous",
            requested_model=body.model or cfg.default_model,
            served_model=served_model,
            provider=prov.name,
            tier=tier,
            decision_reason=reason,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            latency_ms=latency_ms,
        )

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:24]}",
            created=int(time.time()),
            model=served_model,
            choices=[
                ChatCompletionChoice(
                    message=ChatMessage(role="assistant", content=completion.text),
                    finish_reason=completion.finish_reason,
                )
            ],
            usage=Usage(
                prompt_tokens=completion.prompt_tokens,
                completion_tokens=completion.completion_tokens,
                total_tokens=completion.prompt_tokens + completion.completion_tokens,
            ),
            regent={
                "provider": prov.name,
                "tier": tier,
                "decision_reason": reason,
                "latency_ms": latency_ms,
                "cost_micro_usd": cost_micro_usd,
                "cost_usd": round(cost_micro_usd / 1_000_000, 6),
                "task_class": body.task_class,
            },
            )

    @app.get("/dashboard", response_class=Response)
    def dashboard_html():
        html_path = _public / "dashboard.html"
        if not html_path.exists():
            return {"error": "dashboard not found"}
        return FileResponse(html_path)

    return app


app = create_app()
