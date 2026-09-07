from __future__ import annotations

from datetime import UTC, datetime

from eufylocal.db import Database, MeasurementRepository
from eufylocal.models import Measurement


def _measurement(
    weight_kg: float = 80.5,
    impedance_ohm: float | None = 420.0,
    source: str = "advertisement",
) -> Measurement:
    return Measurement(
        measured_at=datetime.now(UTC),
        weight_kg=weight_kg,
        impedance_ohm=impedance_ohm,
        device_id="DEVICE-UUID-123",
        source=source,
        raw_payload_hex="cf00102a00000000000000",
    )


def _repository(tmp_path) -> MeasurementRepository:
    database = Database(tmp_path / "test.db")
    database.initialize()
    return MeasurementRepository(database)


def test_insert_and_latest(tmp_path) -> None:
    repository = _repository(tmp_path)
    repository.insert(_measurement())

    latest = repository.latest()
    assert latest is not None
    assert latest.weight_kg == 80.5
    assert latest.impedance_ohm == 420.0
    assert latest.raw_payload_hex == "cf00102a00000000000000"


def test_null_impedance_is_accepted(tmp_path) -> None:
    repository = _repository(tmp_path)
    repository.insert(_measurement(impedance_ohm=None))
    latest = repository.latest()
    assert latest is not None
    assert latest.impedance_ohm is None


def test_list_returns_newest_first(tmp_path) -> None:
    repository = _repository(tmp_path)
    repository.insert(_measurement(weight_kg=1.0))
    repository.insert(_measurement(weight_kg=2.0))
    repository.insert(_measurement(weight_kg=3.0))

    items = repository.list(limit=10)
    assert [m.weight_kg for m in items] == [3.0, 2.0, 1.0]
    assert repository.list(limit=2)[0].weight_kg == 3.0


def test_latest_empty(tmp_path) -> None:
    repository = _repository(tmp_path)
    assert repository.latest() is None
    assert repository.list() == []
