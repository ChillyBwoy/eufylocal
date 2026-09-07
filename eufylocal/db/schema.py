MEASUREMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measured_at TEXT NOT NULL,
    weight_kg REAL NOT NULL,
    impedance_ohm REAL,
    device_id TEXT NOT NULL,
    source TEXT NOT NULL,
    raw_payload_hex TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_measurements_measured_at
    ON measurements (measured_at DESC);
"""
