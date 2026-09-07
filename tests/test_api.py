from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from eufylocal.db import Database, MeasurementRepository
from eufylocal.main import app, settings
from eufylocal.models import Measurement


def _build_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(settings, "database_path", tmp_path / "api.db")
    monkeypatch.setattr(settings, "ble_enabled", False)
    return TestClient(app)


def test_status_defaults(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        response = client.get("/api/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["bluetooth"]["status"] == "idle"
        assert payload["bluetooth"]["live_weight_active"] is False
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
        assert response.json() == {"measurements": []}


def test_measurements_and_latest(tmp_path, monkeypatch) -> None:
    database = Database(tmp_path / "api.db")
    database.initialize()
    repository = MeasurementRepository(database)
    measurement = Measurement(
        measured_at=datetime.now(UTC),
        weight_kg=77.7,
        impedance_ohm=None,
        device_id="UUID-1",
        source="advertisement",
        raw_payload_hex="cf00000000000000000000",
    )
    repository.insert(measurement)

    client = _build_client(tmp_path, monkeypatch)
    with client:
        status = client.get("/api/status").json()
        assert status["last_measurement"]["weight_kg"] == 77.7

        latest = client.get("/api/measurements/latest").json()
        assert latest["weight_kg"] == 77.7
        assert latest["impedance_ohm"] is None

        listed = client.get("/api/measurements").json()
        assert len(listed["measurements"]) == 1
        assert listed["measurements"][0]["raw_payload_hex"] == "cf00000000000000000000"


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
        javascript = client.get("/static/app.js")
        stylesheet = client.get("/static/style.css")

        assert javascript.status_code == 200
        assert "setInterval(refresh" in javascript.text
        assert stylesheet.status_code == 200
        assert "text/css" in stylesheet.headers["content-type"]


def test_api_routes_have_response_schemas(tmp_path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    with client:
        openapi = client.get("/openapi.json").json()

    assert openapi["paths"]["/api/status"]["get"]["responses"]["200"]["content"]
    assert openapi["paths"]["/api/measurements"]["get"]["responses"]["200"]["content"]
