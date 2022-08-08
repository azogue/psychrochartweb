# -*- coding: utf-8 -*-
"""Extract sensor values from a remote Home Assistant instance."""
import logging
from asyncio import TimeoutError
from itertools import chain
from math import ceil, floor
from pathlib import Path
from time import monotonic
from typing import Any, Dict, Optional, Tuple

from aiohttp import ClientSession, web
from aiohttp.client_exceptions import ClientError, ContentTypeError
from psychrochart.chart import GetStandardAtmPressure, SetUnitSystem, SI
from psychrochart.chartdata import (
    gen_points_in_constant_relative_humidity as w_from_dbt_rh,
)

from .chart_config import ChartCustomConfig
from ..config import AppConfig

_HA_TIMEOUT = 5
KEY_HA_CONFIG = "_ha_config_"

###############################################################################
# Base styles and absolute limits for chart
###############################################################################
MIN_CHART_TEMPERATURE = 20.0
MAX_CHART_TEMPERATURE = 27.0

###############################################################################
# HA Config
###############################################################################
_P_DEFAULT_CONF = Path(__file__).parent.parent / "config" / "default_ha.yaml"


def get_ha_config(app: web.Application) -> ChartCustomConfig:
    return app[KEY_HA_CONFIG]


def set_ha_config(
    app: web.Application, app_config: AppConfig
) -> ChartCustomConfig:
    # Pressure, SI unit system
    SetUnitSystem(SI)
    # Load HA configuration
    path_config = app_config.ha_config_path
    p_ha_conf = (
        path_config
        if path_config.exists() and path_config.is_file()
        else _P_DEFAULT_CONF
    )
    config = ChartCustomConfig.from_yaml_file(p_ha_conf)
    if config.homeassistant.base_pressure is None:
        config.homeassistant.base_pressure = GetStandardAtmPressure(
            config.homeassistant.altitude
        )

    if app_config.SCAN_INTERVAL is not None:
        config.homeassistant.scan_interval = app_config.SCAN_INTERVAL

    # Store config in app
    app[KEY_HA_CONFIG] = config
    return config


###############################################################################
# HA remote polling
###############################################################################
async def _get_states(ha_config: ChartCustomConfig):
    headers = {
        "Authorization": f"Bearer {ha_config.homeassistant.token}",
        "Content-Type": "application/json",
    }
    url_get_sensors = f"{ha_config.homeassistant.host}/api/states"

    async with ClientSession(headers=headers) as session:
        try:
            async with session.get(
                url_get_sensors, timeout=_HA_TIMEOUT
            ) as response:
                response = await response.json()
                return response
        except (ClientError, TimeoutError, ContentTypeError) as exc:
            logging.error(
                f"Cannot update HA states: {exc.__class__.__name__}:{exc}"
            )
            return None


###############################################################################
# Chart data overlay
###############################################################################
def _build_chart_points_and_zones(
    config: ChartCustomConfig, sensor_states: Dict[str, Any]
) -> Tuple[dict, list, float]:
    def _extract_state(states: Dict[str, Any], key: str) -> Optional[float]:
        try:
            state = states[key]
        except KeyError:  # pragma: no cover
            logging.error(f"State not present for entity: {key}")
            return None
        try:
            return float(state["state"])
        except ValueError:  # pragma: no cover
            return None

    points_data = {}
    num_interior = len(config.interior)
    points_int, points_ext = [], []
    for i, p in enumerate(chain(config.interior, config.exterior)):
        if p.temperature in sensor_states and p.humidity in sensor_states:
            temp = _extract_state(sensor_states, p.temperature)
            humid = _extract_state(sensor_states, p.humidity)
            if temp is not None and humid is not None:
                points_data[p.name] = {
                    "xy": (temp, humid),
                    "label": p.name,
                    "style": p.style,
                }
                if i < num_interior:
                    points_int.append(p.name)
                else:
                    points_ext.append(p.name)

    # convex hulls
    zones_data = list(
        filter(
            lambda x: len(x[0]) > 2,
            zip(
                [points_int, points_ext],
                [config.interior_style_line, config.exterior_style_line],
                [config.interior_style_fill, config.exterior_style_fill],
            ),
        )
    )

    pressure = config.homeassistant.base_pressure
    if config.homeassistant.pressure_sensor is not None:
        measured_pressure = _extract_state(
            sensor_states, config.homeassistant.pressure_sensor
        )
        if measured_pressure is not None:
            # from mb to Pa
            pressure = measured_pressure * 100.0

    return points_data, zones_data, pressure


async def get_ha_points_and_zones(ha_config: ChartCustomConfig):
    def _get_entity_id(s):
        return s["entity_id"]

    def _is_sensor_domain(s):
        return _get_entity_id(s).split(".")[0] == "sensor"

    # Poll HA states
    ha_data = await _get_states(ha_config)
    if ha_data is None:
        # empty data
        return {}, [], ha_config.homeassistant.base_pressure

    # filter needed entities
    sensors_needed = ha_config.ha_sensors
    if ha_config.homeassistant.pressure_sensor is not None:
        sensors_needed.append(ha_config.homeassistant.pressure_sensor)

    ha_sensors_data = {
        _get_entity_id(s): s
        for s in filter(_is_sensor_domain, ha_data)
        if _get_entity_id(s) in sensors_needed
    }

    return _build_chart_points_and_zones(ha_config, ha_sensors_data)


def _get_dynamic_limits(points: Dict[str, Any], pressure: float = 101325.0):
    # TODO review estimation of limits
    pairs_t_rh = [point["xy"] for point in points.values()]
    values_w = [w_from_dbt_rh([p[0]], [p[1]], pressure) for p in pairs_t_rh]
    values_t = [p[0] for p in pairs_t_rh]

    min_temp = min(floor((min(values_t) - 1) / 3) * 3, MIN_CHART_TEMPERATURE)
    max_temp = max(ceil((max(values_t) + 1) / 3) * 3, MAX_CHART_TEMPERATURE)

    w_min = min(floor((min(values_w) - 1) / 3) * 3, 5.0)
    w_max = ceil(max(values_w)) + 2

    return min_temp, max_temp, w_min, w_max


async def get_data_for_new_chart(config: ChartCustomConfig):
    tic = monotonic()
    points, zones, pressure = await get_ha_points_and_zones(config)

    if not points:
        return (5, 35), (0, 20), points, zones, pressure

    min_temp, max_temp, w_min, w_max = _get_dynamic_limits(points, pressure)
    logging.info(
        f"Got data from HA: {len(points)} points, "
        f"new limits: T={min_temp, max_temp}, w={w_min, w_max}, P={pressure}. "
        f"Took {monotonic() - tic:.3f} s"
    )
    return (min_temp, max_temp), (w_min, w_max), points, zones, pressure
