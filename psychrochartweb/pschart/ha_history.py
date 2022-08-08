# -*- coding: utf-8 -*-
"""Handle history of extracted values from a remote Home Assistant instance."""
import logging
from collections import deque
from time import monotonic
from typing import Any, Dict, Tuple

import matplotlib.colors as mcolors
from aiohttp import web

from .chart_config import ChartCustomConfig

KEY_HISTORY = "_ha_history"


def set_ha_history(app: web.Application, ha_config: ChartCustomConfig):
    num_samples = (
        ha_config.homeassistant.delta_arrows
        // ha_config.homeassistant.scan_interval
    )
    app[KEY_HISTORY] = deque([], num_samples)
    logging.info(f"HA history up to {num_samples} samples (evolution arrows)")


def _arrow_style(style):
    if "color" in style:
        color = style["color"]
        if isinstance(color, str) and mcolors.is_color_like(color):
            color = list(mcolors.to_rgb(color))
        else:
            color = list(color)
    else:
        color = [1, 0.8, 0.1]
    if "alpha" in style:
        color += [style["alpha"]]
    elif len(color) == 3:
        color += [0.6]
    return {"color": color, "arrowstyle": "wedge"}


async def update_history(
    app: web.Application, points: Dict[str, Any]
) -> Tuple[Dict[str, Any], float]:
    """Accumulate timestamped sets of points to build time evolution arrows."""
    now = monotonic()
    data = app[KEY_HISTORY]
    data.append((now, points))

    oldest = data[0][0]
    oldest_points = data[0][1]
    age = now - oldest
    n_samples = len(data)
    logging.info(f"History has {n_samples} samples, with age: {age:.1f} sec")

    if n_samples < 3:
        return {}, 0.0

    arrows = {
        k: {
            "xy": [p["xy"], oldest_points[k]["xy"]],
            "style": _arrow_style(p["style"]),
        }
        for k, p in points.items()
        if k in oldest_points
        # TODO better equality
        and p != oldest_points[k]
    }

    return arrows, age
