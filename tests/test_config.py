from eufylocal.config import Settings


def test_settings_load_dotenv(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            (
                "EUFYLOCAL_DEVICE_IDENTIFIER=DEVICE-UUID",
                "EUFYLOCAL_TRANSPORT=gatt",
                "EUFYLOCAL_HOST=0.0.0.0",
                "EUFYLOCAL_PORT=9000",
                "EUFYLOCAL_BLE_ENABLED=false",
                "EUFYLOCAL_AUTO_MIGRATE=false",
                "EUFYLOCAL_DB_HOST=db",
                "EUFYLOCAL_DB_PORT=5433",
                "EUFYLOCAL_DB_NAME=custom",
                "EUFYLOCAL_DB_USER=user",
                "EUFYLOCAL_DB_PASSWORD=password",
            )
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.device_identifier == "DEVICE-UUID"
    assert settings.transport == "gatt"
    assert settings.host == "0.0.0.0"
    assert settings.port == 9000
    assert settings.ble_enabled is False
    assert settings.auto_migrate is False
    assert settings.db_host == "db"
    assert settings.db_port == 5433
    assert settings.db_name == "custom"
    assert settings.db_user == "user"
    assert settings.db_password == "password"
    assert settings.db_url == "postgresql+psycopg://user:password@db:5433/custom"
