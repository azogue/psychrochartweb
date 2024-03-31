import asyncio
import logging
import warnings
from collections import deque
from contextlib import suppress
from math import ceil
from time import monotonic
from typing import Any

import matplotlib.colors as mcolors
from psychrochart.chart import GetStandardAtmPressure, SetUnitSystem, SI
from pydantic import BaseModel, ConfigDict

from psychrochartweb.pschart.ha_remote_polling import get_data_for_new_chart
from psychrochartweb.pschart.make_chart import plot_chart

from .config import Settings
from .pschart.chart_config import ChartCustomConfig


class ChartHandler(BaseModel):
    settings: Settings
    ha_config: ChartCustomConfig
    ha_history: deque[tuple[float, dict[str, Any]]]
    current_svg_chart: bytes | None = None

    _task_ha_polling: asyncio.Task | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def create(cls, settings: Settings):
        # Pressure, SI unit system
        SetUnitSystem(SI)
        # Load HA configuration
        config = ChartCustomConfig.from_yaml_file(settings.ha_config_path)
        if config.homeassistant.base_pressure is None:
            config.homeassistant.base_pressure = GetStandardAtmPressure(
                config.homeassistant.altitude
            )
        num_samples = config.homeassistant.delta_arrows // int(
            ceil(config.homeassistant.scan_interval)
        )
        logging.info(
            f"HA history up to {num_samples} samples (evolution arrows)"
        )
        handler = cls(
            settings=settings,
            ha_config=config,
            ha_history=deque([], num_samples),
        )
        handler._task_ha_polling = None
        return handler

    async def start(self) -> None:
        await self.make_chart()
        loop = asyncio.get_running_loop()
        self._task_ha_polling = loop.create_task(
            self._periodic_polling(), name="HA-POLLING"
        )

    async def stop(self) -> None:
        if (
            self._task_ha_polling is not None
            and not self._task_ha_polling.done()
        ):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                self._task_ha_polling.cancel()
                with suppress(asyncio.CancelledError):
                    await self._task_ha_polling
            self._task_ha_polling = None

    async def _periodic_polling(self) -> None:
        period = self.ha_config.homeassistant.scan_interval
        logging.warning(
            "Starting periodic poll to rebuild psychrochart (%.1f s)", period
        )
        while True:
            await asyncio.sleep(period)
            await self.make_chart()
            logging.debug("Chart updated, sleeping %.1f secs", period)

    @staticmethod
    def _arrow_style(style: dict[str, Any]) -> dict[str, Any]:
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
        self, points: dict[str, Any]
    ) -> tuple[dict[str, Any], float]:
        """Accumulate timestamped sets of points to build evolution arrows."""
        now = monotonic()
        self.ha_history.append((now, points))
        oldest, oldest_points = self.ha_history[0]
        age = now - oldest
        n_samples = len(self.ha_history)
        logging.info(
            f"History has {n_samples} samples, with age: {age:.1f} sec"
        )

        if n_samples < 3:
            return {}, 0.0

        arrows = {
            k: {
                "xy": [p["xy"], oldest_points[k]["xy"]],
                "style": self._arrow_style(p["style"]),
            }
            for k, p in points.items()
            if k in oldest_points
            # TODO better equality
            and p != oldest_points[k]
        }

        return arrows, age

    async def make_chart(self) -> None:
        tic_0 = monotonic()

        # conf = get_ha_config(app)
        rg_dbt, rg_w, points, zones, pressure = await get_data_for_new_chart(
            self.ha_config
        )
        arrows, age = await self.update_history(points)

        tic = monotonic()
        bytes_svg_data = await plot_chart(
            rg_dbt, rg_w, pressure, points, zones, arrows, age
        )
        self.current_svg_chart = bytes_svg_data
        toc = monotonic()
        logging.info(
            f"SVG CREATED ({len(bytes_svg_data) / 1024.0:.2f} kB), "
            f"chart plotted in {toc - tic:.3f} s, "
            f"total time: {toc - tic_0:.3f} s"
        )
