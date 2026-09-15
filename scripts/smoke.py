"""One-command offline smoke test.

Runs the whole pipeline (route -> complete -> ledger) in process with no
credentials, so anyone can verify the gateway works before setting up keys.
Writes to a throwaway ledger, so running it never pollutes real usage data.
Exits non-zero on failure, which is why CI calls it directly.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Running this file directly puts `scripts/` on sys.path, not the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from src.app import create_app  # noqa: E402
from src.config import Settings  # noqa: E402


def main() -> int:
    db_path = Path(tempfile.mkdtemp(prefix="regent-smoke-")) / "smoke.db"
    settings = Settings(
        db_path=db_path,
        default_provider="stub",
        default_model="stub-small",
        admin_key="smoke-only",
        provider_api_key=None,
    )

    with TestClient(create_app(settings)) as client:
        health = client.get("/healthz")
        assert health.status_code == 200, health.text
        print("healthz:", health.json())

        reply = client.post(
            "/v1/chat/completions",
            json={
                "model": "stub-small",
                "messages": [{"role": "user", "content": "classify: invoice overdue"}],
                "task_class": "classification",
            },
        )
        assert reply.status_code == 200, reply.text
        body = reply.json()
        print("reply:", body["choices"][0]["message"]["content"])
        print("why:", body["regent"]["decision_reason"])

        usage = client.get("/v1/usage")
        assert usage.status_code == 200, usage.text
        assert usage.json()["calls"] == 1, usage.json()
        print("usage:", usage.json())

    print(f"smoke test passed (throwaway ledger at {db_path})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
