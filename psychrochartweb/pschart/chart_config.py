# -*- coding: utf-8 -*-
import logging
from itertools import chain
from pathlib import Path
from typing import Any, Dict, List, Optional

import attr
import cattr
from yaml import safe_load

EXT_ZONE_LINE = {"color": "darkblue", "lw": 1, "alpha": 0.5, "ls": "--"}
EXT_ZONE_FILL = {"color": "darkblue", "lw": 0, "alpha": 0.3}
INT_ZONE_LINE = {"color": "darkgreen", "lw": 2, "alpha": 0.5, "ls": ":"}
INT_ZONE_FILL = {"color": "darkgreen", "lw": 0, "alpha": 0.3}


@attr.s
class SensorPoint:
    """
    Pair of temperature and humidity HA entities,
    labeled and with customized matplotlib styling.
    """

    name: str = attr.ib()
    temperature: str = attr.ib()
    humidity: str = attr.ib()
    style: Dict[str, Any] = attr.ib(factory=dict)


@attr.s
class HAConfig:
    """
    Group of SensorPoints, to be grouped and, optionally, .
    Common use of this grouping is to differentiate external sensors
    from internal ones.
    """

    host: str = attr.ib(factory=str)
    token: str = attr.ib(factory=str)

    altitude: int = attr.ib(default=100)
    base_pressure: Optional[float] = attr.ib(default=None)
    pressure_sensor: Optional[str] = attr.ib(default=None)
    scan_interval: int = attr.ib(default=30)
    delta_arrows: int = attr.ib(default=3600)


@attr.s
class ChartCustomConfig:
    """
    Configuration of the psychrochart,
     * with overlay of HA sensors,
     * grouped in interior / exterior zones.
    """

    homeassistant: HAConfig = attr.ib()
    interior: List[SensorPoint] = attr.ib(factory=list)
    exterior: List[SensorPoint] = attr.ib(factory=list)
    interior_style_line: Dict[str, Any] = attr.ib(factory=EXT_ZONE_LINE.copy)
    interior_style_fill: Dict[str, Any] = attr.ib(factory=EXT_ZONE_FILL.copy)
    exterior_style_line: Dict[str, Any] = attr.ib(factory=INT_ZONE_LINE.copy)
    exterior_style_fill: Dict[str, Any] = attr.ib(factory=INT_ZONE_FILL.copy)

    @classmethod
    def from_yaml_file(cls, path_config: Path):
        """Read configuration from a yaml file."""
        raw_data: dict = safe_load(
            path_config.read_text(encoding="utf-8")
        )
        try:
            return cattr.structure_attrs_fromdict(raw_data, cls)
        except (ValueError, TypeError) as exc:  # pragma: no cover
            logging.error(
                f"Bad config import from {path_config}: {exc}. "
                f"Raw data is {raw_data}. Using empty one"
            )
            return cls(homeassistant=HAConfig())

    @property
    def ha_sensors(self) -> List[str]:
        """List all HomeAssistant entities used in the chart."""
        return [
            entity
            for sensor in chain(self.interior, self.exterior)
            for entity in (sensor.temperature, sensor.humidity)
        ]
