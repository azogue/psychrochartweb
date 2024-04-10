# -*- coding: utf-8 -*-
from itertools import chain
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from yaml import safe_load

EXT_ZONE_LINE = {"color": "darkblue", "lw": 1, "alpha": 0.5, "ls": "--"}
EXT_ZONE_FILL = {"color": "darkblue", "lw": 0, "alpha": 0.3}
INT_ZONE_LINE = {"color": "darkgreen", "lw": 2, "alpha": 0.5, "ls": ":"}
INT_ZONE_FILL = {"color": "darkgreen", "lw": 0, "alpha": 0.3}


class SensorPoint(BaseModel):
    """
    Pair of temperature and humidity HA entities,
    labeled and with customized matplotlib styling.
    """

    name: str
    temperature: str
    humidity: str
    style: dict[str, Any] = Field(default_factory=dict)


class HAConfig(BaseModel):
    """
    Group of SensorPoints, to be grouped and, optionally, .
    Common use of this grouping is to differentiate external sensors
    from internal ones.
    """

    # TODO evolve to URL + secret
    host: str = ""
    token: str = ""

    altitude: int = 100
    base_pressure: float | None = None
    pressure_sensor: str | None = None
    scan_interval: int | float = Field(default=30, gt=0, le=3600 * 24 * 7)
    delta_arrows: int = Field(default=3600, ge=1, le=3600 * 24)


class ChartCustomConfig(BaseModel):
    """
    Configuration of the psychrochart,
     * with overlay of HA sensors,
     * grouped in interior / exterior zones.
    """

    homeassistant: HAConfig
    interior: list[SensorPoint] = Field(default_factory=list)
    exterior: list[SensorPoint] = Field(default_factory=list)
    interior_style_line: dict[str, Any] = Field(
        default_factory=EXT_ZONE_LINE.copy
    )
    interior_style_fill: dict[str, Any] = Field(
        default_factory=EXT_ZONE_FILL.copy
    )
    exterior_style_line: dict[str, Any] = Field(
        default_factory=INT_ZONE_LINE.copy
    )
    exterior_style_fill: dict[str, Any] = Field(
        default_factory=INT_ZONE_FILL.copy
    )

    @classmethod
    def from_yaml_file(cls, path_config: Path):
        """Read configuration from a yaml file."""
        raw_data = safe_load(path_config.read_text(encoding="utf-8"))
        return cls.model_validate(raw_data)

    @property
    def ha_sensors(self) -> list[str]:
        """List all HomeAssistant entities used in the chart."""
        return [
            entity
            for sensor in chain(self.interior, self.exterior)
            for entity in (sensor.temperature, sensor.humidity)
        ]
