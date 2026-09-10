from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from eufylocal.parser import extract_frame_from_manufacturer_data, parse_frame
from eufylocal.schemas.frame import ParsedFrame

MODEL_MARKER = b"\x91\x46"


def parse_advertisement(
    _device: BLEDevice,
    advertisement: AdvertisementData,
) -> ParsedFrame | None:
    for raw in advertisement.manufacturer_data.values():
        if not raw.endswith(MODEL_MARKER):
            continue

        frame = extract_frame_from_manufacturer_data(raw)
        if frame is None:
            continue

        parsed_frame = parse_frame(frame)
        if parsed_frame is None:
            continue

        return parsed_frame

    return None


async def scan() -> AsyncGenerator[ParsedFrame]:
    frames: asyncio.Queue[ParsedFrame] = asyncio.Queue()

    def on_advertisement(device: BLEDevice, advertisement: AdvertisementData) -> None:
        parsed_frame = parse_advertisement(device, advertisement)
        if parsed_frame is not None:
            frames.put_nowait(parsed_frame)

    scanner = BleakScanner(detection_callback=on_advertisement)
    await scanner.start()
    try:
        while True:
            yield await frames.get()
    finally:
        await scanner.stop()
