# -*- coding: utf-8 -*-
"""The app configuration module."""
import asyncio
import logging
from time import monotonic

from aiohttp import web
from aiojobs import Scheduler
from aiojobs.aiohttp import (
    get_scheduler_from_app,
    setup as setup_periodic_jobs,
)

from .config import AppConfig, CONFIG_KEY, NAME_KEY
from .logger import get_app_logger, set_app_logger
from .pschart import (
    get_ha_config,
    make_chart,
    set_ha_config,
    set_ha_history,
)
from .routes import routes


async def _periodic_task_scheduler(app: web.Application):
    scheduler: Scheduler = get_scheduler_from_app(app)
    period = get_ha_config(app).homeassistant.scan_interval
    logging.warning(
        f"Starting scheduler to rebuild psychrochart periodically ({period} s)"
    )
    while True:
        await asyncio.sleep(period)
        await scheduler.spawn(make_chart(app))
        logging.debug(f"Task spawned, sleeping {period:.1f} secs")


async def _app_startup(app: web.Application):
    tic = monotonic()
    logger = get_app_logger(app, "start_up")
    scheduler: Scheduler = get_scheduler_from_app(app)
    # Initial chart
    await make_chart(app)
    await scheduler.spawn(_periodic_task_scheduler(app))
    logger.warning(f"App startup done in {monotonic() - tic:.2f} s.")


async def _app_cleanup(app: web.Application):
    logger = get_app_logger(app, "clean_up")
    logger.debug("App cleanup start")
    scheduler: Scheduler = get_scheduler_from_app(app)

    # gracefully close spawned jobs
    await scheduler.close()
    logger.debug("App cleanup finished")


def create_app(
    name: str = "pschart", config: AppConfig = None,
) -> web.Application:
    """Psychrochart web application creation."""
    config = config if config is not None else AppConfig()
    # Create base aiohttp application
    app = web.Application()
    app.router.add_routes(routes)

    # Setup app name, config & debug mode
    app[NAME_KEY] = name
    app[CONFIG_KEY] = config
    set_app_logger(app, config)
    logger = get_app_logger(app, "build")
    logging.getLogger("psychrochart").setLevel(logging.WARNING)

    # Setup HA config and periodic polling
    ha_conf = set_ha_config(app, config)
    set_ha_history(app, ha_conf)
    setup_periodic_jobs(app)
    app.on_startup.append(_app_startup)
    app.on_cleanup.append(_app_cleanup)

    logger.info("App initialized.")

    return app
