from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import eufylocal.main as main_module
import eufylocal.runtime.runtime as runtime_module
from eufylocal.db import MeasurementModel, MeasurementRepository
from eufylocal.db.migration import upgrade_database
from eufylocal.main import app, settings


def _build_client(tmp_path, monkeypatch) -> TestClient:
    db_url = URL.create(
        "sqlite+aiosqlite",
        database=str(tmp_path / "api.db"),
    ).render_as_string(hide_password=False)
    upgrade_database(db_url)
    engine = create_async_engine(db_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(settings, "db_url", db_url)
    monkeypatch.setattr(settings, "ble_enabled", False)
    monkeypatch.setattr(settings, "auto_migrate", False)
    monkeypatch.setattr(main_module.db_session, "engine", engine)
    monkeypatch.setattr(main_module.db_session, "AsyncSessionLocal", session_factory)
    return TestClient(app)


def test_status_defaults(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        response = client.get("/api/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["bluetooth"]["status"] == "idle"
        assert payload["bluetooth"]["live_weight_active"] is False
        assert payload["bluetooth"]["last_received_at"] is None
        assert payload["last_measurement"] is None


def test_latest_empty_returns_null(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        response = client.get("/api/measurements/latest")
        assert response.status_code == 200
        assert response.json() is None


def test_measurements_empty_list(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        response = client.get("/api/measurements")
        assert response.status_code == 200
        assert response.json() == []


def test_measurements_and_latest(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    measurement = MeasurementModel(
        measured_at=datetime.now(UTC),
        weight_kg=77.7,
        impedance_ohm=None,
        device_id="UUID-1",
        source="advertisement",
        raw_payload_hex="cf00000000000000000000",
    )

    async def insert_measurement() -> None:
        async with main_module.db_session.AsyncSessionLocal() as session:
            await MeasurementRepository(session).insert(measurement)

    asyncio.run(insert_measurement())

    with client:
        status = client.get("/api/status").json()
        assert status["last_measurement"]["weight_kg"] == 77.7
        last_received_at = datetime.fromisoformat(status["bluetooth"]["last_received_at"])
        assert last_received_at == measurement.measured_at

        latest = client.get("/api/measurements/latest").json()
        assert latest["weight_kg"] == 77.7
        assert latest["impedance_ohm"] is None

        listed = client.get("/api/measurements").json()
        assert len(listed) == 1
        assert listed[0]["raw_payload_hex"] == "cf00000000000000000000"


def test_measurements_limit_validation(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        assert client.get("/api/measurements?limit=0").status_code == 422
        assert client.get("/api/measurements?limit=9999").status_code == 422


def test_index_served(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        response = client.get("/")
        assert response.status_code == 200
        assert "eufylocal" in response.text


def test_static_assets_are_served(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        index = client.get("/")
        asset_paths = re.findall(r'(?:src|href)="(/assets/[^"]+)"', index.text)
        assets = [client.get(path) for path in asset_paths]

        assert len(assets) == 2
        assert all(asset.status_code == 200 for asset in assets)
        assert any("/api/status" in asset.text for asset in assets)
        assert any("text/css" in asset.headers["content-type"] for asset in assets)


def test_api_routes_have_response_schemas(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        openapi = client.get("/openapi.json").json()

    assert openapi["paths"]["/api/status"]["get"]["responses"]["200"]["content"]
    assert openapi["paths"]["/api/measurements"]["get"]["responses"]["200"]["content"]


def test_lifespan_stops_collector(tmp_path, monkeypatch) -> None:
    calls: list[str] = []

    class FakeCollector:
        def __init__(self, _runtime, _frame_handler) -> None:
            self.stopped = asyncio.Event()

        async def run(self) -> None:
            calls.append("run")
            await self.stopped.wait()

        async def stop(self) -> None:
            calls.append("stop")
            self.stopped.set()

    client = _build_client(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "ble_enabled", True)
    monkeypatch.setattr(runtime_module, "BLECollector", FakeCollector)

    with client:
        assert client.get("/api/status").status_code == 200

    assert calls == ["run", "stop"]
