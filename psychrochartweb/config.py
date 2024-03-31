import importlib.metadata
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

_API_VERSION = importlib.metadata.version("psychrochartweb")

# path to custom HA configuration
_P_DEFAULT_CONF = Path(__file__).parent / "config" / "default_ha.yaml"
P_CUSTOM_CONFIG = _P_DEFAULT_CONF.parent
HA_CONFIG = "custom_ha_sensors.yaml"


class Settings(BaseSettings):
    """App settings to configure a physical IBIS-IP-compatible device."""

    version: str = Field(default=_API_VERSION)
    app_port: int = Field(default=8081)
    app_log_level: str = "INFO"
    app_log_level_components: dict[str, str] = Field(default_factory=dict)

    ha_config_name: str = Field(default=HA_CONFIG)
    custom_folder: Path = Field(default=P_CUSTOM_CONFIG)

    @property
    def ha_config_path(self) -> Path:
        """Return path for HomeAssistant config, under 'custom' folder."""
        path_config = self.custom_folder / self.ha_config_name
        p_ha_conf = (
            path_config
            if path_config.exists() and path_config.is_file()
            else _P_DEFAULT_CONF
        )
        assert p_ha_conf.exists(), p_ha_conf
        return p_ha_conf

    # pydantic config to tune Settings
    model_config = SettingsConfigDict(
        extra="ignore",
        arbitrary_types_allowed=False,
        validate_default=True,
        case_sensitive=False,
        env_prefix="",
        env_file=[Path(".env")],
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        secrets_dir=None,
    )


if __name__ == "__main__":
    print(Settings().model_dump_json(indent=2, exclude_defaults=True))
