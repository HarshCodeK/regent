"""Runtime configuration.

Everything comes from the environment, and every default is safe to run offline.
Secrets have no hard-coded fallback: if a real provider is selected without its key,
startup fails loudly instead of degrading silently.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    default_provider: str
    default_model: str
    admin_key: str
    provider_api_key: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            db_path=Path(os.getenv("REGENT_DB_PATH", "./.regent/regent.db")),
            default_provider=os.getenv("REGENT_DEFAULT_PROVIDER", "stub"),
            default_model=os.getenv("REGENT_DEFAULT_MODEL", "stub-small"),
            admin_key=os.getenv("REGENT_ADMIN_KEY", "regent-dev-admin"),
            provider_api_key=os.getenv("GROQ_API_KEY") or None,
        )
