# -*- coding: utf-8 -*-
import logging
from time import monotonic

from aiohttp import web

from .chart_config import ChartCustomConfig
from .ha_history import set_ha_history, update_history
from .ha_remote_polling import (
    get_data_for_new_chart,
    get_ha_config,
    set_ha_config,
)
from .make_chart import plot_chart
from ..config import SVG_BYTES


__all__ = (
    "ChartCustomConfig",
    "set_ha_config",
    "set_ha_history",
    "get_ha_config",
    "make_chart",
)


async def make_chart(app: web.Application):
    tic_0 = monotonic()
    conf = get_ha_config(app)
    rg_dbt, rg_w, points, zones, pressure = await get_data_for_new_chart(conf)
    arrows, age = await update_history(app, points)

    tic = monotonic()
    bytes_svg_data = await plot_chart(
        rg_dbt, rg_w, pressure, points, zones, arrows, age
    )

    app[SVG_BYTES] = bytes_svg_data

    toc = monotonic()
    logging.info(
        f"SVG CREATED ({len(bytes_svg_data) / 1024.0:.2f} kB), "
        f"chart plotted in {toc - tic:.3f} s, total time: {toc - tic_0:.3f} s"
    )
    return bytes_svg_data, points
