"""Shared fixtures. Every test runs against a throwaway SQLite file in tmp_path,
so no test can ever touch a developer's real ledger."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app import create_app
from src.config import Settings


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "regent.db",
        default_provider="stub",
        default_model="stub-small",
        admin_key="test-admin-key",
        provider_api_key=None,
    )


@pytest.fixture()
def client(settings: Settings) -> TestClient:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
