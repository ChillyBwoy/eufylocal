# eufylocal

A local Bluetooth LE bridge for the **eufy Smart Scale C1 (T9146)**.

The application works entirely offline. The MacBook acts as the BLE client and local HTTP
server, while PostgreSQL stores measurements locally. It does not require eufyLife, an account,
internet access, or third-party services.

## Features

* Scans for BLE devices and discovers scales named `eufy T9146`.
* Reads weight and, when available, impedance from advertising packets without connecting,
  or through GATT (`0xFFF0` with notifications on `0xFFF4`).
* Stores the UTC timestamp, weight in kilograms, impedance, device identifier, data source,
  and raw hexadecimal payload in PostgreSQL through the SQLAlchemy 2.x async engine.
* Provides a local web interface and HTTP API.
* Never sends the history-clear command (`F2 01`) or writes any other data to the scale.

## Requirements

* Python 3.14
* macOS with Bluetooth LE
* PostgreSQL 16 (a Compose service is included for local development)

## Installation

Using uv:

```bash
make install
```

This installs both the Python dependencies with `uv` and the frontend dependencies with `npm`.

Start the local PostgreSQL service before running the application or tests:

```bash
make db-start
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

For frontend development, run both Vite and the API server:

```bash
make dev
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` requests to the FastAPI server on port `8000`.
The backend continues to serve the last production frontend build at port `8000`.

Build the production Vue application and Python distributions with:

```bash
make build
```

The Vite output is written to `eufylocal/static/` and packaged into the Python wheel.

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
EUFYLOCAL_AUTO_MIGRATE=true
EUFYLOCAL_HOST=127.0.0.1
EUFYLOCAL_PORT=8000
EUFYLOCAL_DB_HOST=127.0.0.1
EUFYLOCAL_DB_PORT=5432
EUFYLOCAL_DB_NAME=eufylocal
EUFYLOCAL_DB_USER=eufylocal
EUFYLOCAL_DB_PASSWORD=eufylocal
EUFYLOCAL_LOG_LEVEL=INFO
```

Supported transports are `advertisement`, `gatt`, and `both`. Advertising is the recommended
default because T9146 broadcasts measurements without requiring a connection.

## Database Migrations

Alembic migrations are applied automatically at startup when `EUFYLOCAL_AUTO_MIGRATE=true`,
which is the default. They can also be managed explicitly:

```bash
make db-up
make db-current
make db-down
make db-rev MESSAGE="add a column"
```

All SQLAlchemy and Alembic files are contained in `eufylocal/db/`. The initial migration creates
the append-only `measurements` table and indexes for complete and final-only timelines in
PostgreSQL. Existing SQLite databases are not migrated.

Generate 3–4 development measurements for the last week:

```bash
make db-seed
```

Use `make db-seed WEEKS=12` to generate the same sampling frequency across a longer period. The
command only connects to PostgreSQL on localhost and replaces its previous `DEV-SCALE` records
without deleting real measurements.

## HTTP API

* `GET /api/status` returns Bluetooth status, live weight, and the latest measurement.
* `GET /api/measurements?limit=50` returns final measurements in descending timestamp order.
* `GET /api/measurements?limit=50&final_only=false` returns every stored BLE frame.
* `GET /api/measurements/latest` returns the latest final measurement or `null`.
* `GET /api/events` streams SSE notifications when the REST data should be refreshed.

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

Weight is always transmitted in kilograms, regardless of the scale's display unit. Every valid
frame is stored without deduplication. Intermediate and final measurements are distinguished by
the `is_final` field; the HTTP history returns only final measurements by default.

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
