from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


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
    auto_migrate: bool = True
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    db_host: str = "127.0.0.1"
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = "eufylocal"
    db_user: str = "eufylocal"
    db_password: str = "eufylocal"
    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"] = "INFO"

    @property
    def db_url(self) -> str:
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)


settings = Settings()
