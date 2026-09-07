# eufylocal

A local Bluetooth LE bridge for the **eufy Smart Scale C1 (T9146)**.

The application works entirely offline. The MacBook acts as the BLE client, local HTTP
server, and measurement storage. It does not require eufyLife, an account, internet access,
or third-party services.

## Features

* Scans for BLE devices and discovers scales named `eufy T9146`.
* Reads weight and, when available, impedance from advertising packets without connecting,
  or through GATT (`0xFFF0` with notifications on `0xFFF4`).
* Stores the UTC timestamp, weight in kilograms, impedance, device identifier, data source,
  and raw hexadecimal payload in SQLite.
* Provides a local web interface and HTTP API.
* Never sends the history-clear command (`F2 01`) or writes any other data to the scale.

## Requirements

* Python 3.14
* macOS with Bluetooth LE

## Installation

Using uv:

```bash
uv sync
```

Using a virtual environment:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## macOS Bluetooth Permission

macOS requests Bluetooth permission separately for each application. Accept the system prompt
when the application starts for the first time.

If the prompt does not appear or access was previously denied:

1. Open **System Settings > Privacy & Security > Bluetooth**.
2. Enable the Python interpreter, Terminal, or iTerm used to run the application.
3. If necessary, run `sudo tccutil reset Bluetooth`, restart the application, and grant access
   again.

## Running The Server

```bash
uv run eufylocal serve
# or
make run
```

The server listens on `127.0.0.1:8000` by default. Open
<http://127.0.0.1:8000> in a browser.

To access the interface from a phone on the local network:

```bash
uv run eufylocal serve --host 0.0.0.0
# or
make run HOST=0.0.0.0
```

You can also set `EUFYLOCAL_HOST=0.0.0.0` in `.env`. Then open
`http://<mac-ip-address>:8000` from the phone.

## Device Discovery

Discover the scale identifier:

```bash
uv run eufylocal scan
# or
make scan TIMEOUT=10
```

Capture repeated raw BLE payloads for diagnostics:

```bash
uv run eufylocal dump --timeout 30
# or
make dump TIMEOUT=30
```

Create the local configuration after discovering the scale:

```bash
cp .env.example .env
```

Set `EUFYLOCAL_DEVICE_IDENTIFIER` to the discovered UUID.

## Configuration

Settings are loaded from environment variables and the `.env` file in the working directory.
Environment variables take precedence over values in `.env`.

```dotenv
EUFYLOCAL_DEVICE_IDENTIFIER=AAAA1111-...
EUFYLOCAL_TRANSPORT=advertisement
EUFYLOCAL_HOST=127.0.0.1
EUFYLOCAL_PORT=8000
EUFYLOCAL_DATABASE_PATH=eufylocal.db
EUFYLOCAL_LOG_LEVEL=INFO
```

Supported transports are `advertisement`, `gatt`, and `both`. Advertising is the recommended
default because T9146 broadcasts measurements without requiring a connection.

## HTTP API

* `GET /api/status` returns Bluetooth status, live weight, and the latest measurement.
* `GET /api/measurements?limit=50` returns measurements in descending timestamp order.
* `GET /api/measurements/latest` returns the latest measurement or `null`.

## T9146 Protocol

A measurement frame is 11 bytes and starts with `CF`:

| Byte | Meaning |
| ---- | ------- |
| 0 | `0xCF` marker |
| 1-2 | Little-endian impedance divided by 10, in ohms |
| 3-4 | Little-endian weight divided by 100, in kilograms |
| 8 | Display-unit bit 0: 0 for kg, 1 for lb |
| 9 | Status: `0x00` is stable, `0x02` means the weight limit was exceeded |
| 10 | XOR checksum of bytes 0-9 |

Advertising manufacturer data has this layout:
`[6-byte MAC][11-byte frame][1-byte battery][0x9146 model]`.

Weight is always transmitted in kilograms, regardless of the scale's display unit. Only stable
final measurements are stored. Intermediate weight is displayed live but is not added to history.

## Why Not `eufylife-ble-client`

Version 0.1.10 of `eufylife-ble-client` supports T9146, but its public API exposes only processed
weight state. It does not expose the raw payload, data source, or impedance separately. Parsing is
therefore implemented locally in `eufylocal/parser.py` using the verified frame format.

## Quality Checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
# or run every check at once
make check
```

Parser tests use previously captured real T9146 BLE payloads.

## macOS Device Identifiers

macOS does not expose BLE MAC addresses to applications. CoreBluetooth provides a device UUID
instead, so `EUFYLOCAL_DEVICE_IDENTIFIER` must contain that UUID rather than a MAC address. The
scale's MAC address is also embedded in manufacturer data and is logged for diagnostics.

## Project Structure

* `eufylocal/main.py` contains the FastAPI app, lifecycle, CLI, and frontend routes.
* `eufylocal/routes/` contains the status and measurement API routes.
* `eufylocal/schemas.py` contains the Pydantic response schemas.
* `eufylocal/db/` contains the SQLite connection, schema, and measurement repository.
* `eufylocal/ble_collector.py` contains the advertising and GATT collector.
* `eufylocal/parser.py` decodes T9146 frames.
