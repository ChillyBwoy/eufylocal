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
