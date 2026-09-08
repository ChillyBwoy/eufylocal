from eufylocal.ble_collector import BLECollector
from eufylocal.db import MeasurementRepository
from eufylocal.runtime.app_state import AppState
from eufylocal.runtime.measurement_handler import MeasurementHandler
from eufylocal.runtime.measurement_writer import MeasurementWriter


def create_runtime(
    repository: MeasurementRepository,
) -> tuple[AppState, BLECollector]:
    state = AppState()
    writer = MeasurementWriter(repository)
    handler = MeasurementHandler(state.apply, writer)
    collector = BLECollector(state.apply, handler.handle_frame)
    return state, collector
