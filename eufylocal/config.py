from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="EUFYLOCAL_",
        extra="ignore",
    )

    device_identifier: str | None = None
    transport: Literal["advertisement", "gatt", "both"] = "advertisement"
    scan_timeout: float = Field(default=5.0, gt=0)
    continuous_scan: bool = True
    ble_enabled: bool = True
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    database_path: Path = Path("eufylocal.db")
    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"] = "INFO"
