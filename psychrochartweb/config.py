# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

import attr
from aiohttp import web
from envparse import env

# path to custom HA configuration
P_CUSTOM_CONFIG = Path(__file__).parent.parent / "custom"
HA_CONFIG = "custom_ha_sensors.yaml"

# app keys
NAME_KEY = "name"
CONFIG_KEY = "_config"
SVG_BYTES = "chart_svg_bytes"


@attr.s
class AppConfig:
    """Configuration of the aiohttp application."""

    HOST: str = attr.ib(default=env.str("HOST", default="0.0.0.0"))
    PORT: int = attr.ib(default=env.int("PORT", default=80))
    LOGGING_LEVEL: str = attr.ib(
        default=env.str("LOGGING_LEVEL", default="INFO")
    )

    SCAN_INTERVAL: Optional[int] = attr.ib(
        default=env.str("SCAN_INTERVAL", default=None)
    )
    HA_CONFIG_NAME: str = attr.ib(
        default=env.str("HA_CONFIG_NAME", default=HA_CONFIG)
    )
    CUSTOM_FOLDER: Path = attr.ib(
        default=Path(env.str("CUSTOM_FOLDER", default=P_CUSTOM_CONFIG))
    )

    def __attrs_post_init__(self):
        if self.SCAN_INTERVAL:
            self.SCAN_INTERVAL = int(self.SCAN_INTERVAL)
        else:
            self.SCAN_INTERVAL = None

    @property
    def ha_config_path(self) -> Path:
        """Return path for HomeAssistant config, under 'custom' folder."""
        return self.CUSTOM_FOLDER / self.HA_CONFIG_NAME


def get_config(app: web.Application) -> AppConfig:
    """Retrieve app configuration dataclass."""
    return app[CONFIG_KEY]
