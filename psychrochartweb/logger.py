# -*- coding: utf-8 -*-
"""The app configuration module."""
import logging

from aiohttp import web

from .config import AppConfig, NAME_KEY


def get_app_logger(app, logger_name=None) -> logging.Logger:
    app_name = app[NAME_KEY]
    logging_key = ".".join(filter(bool, (app_name, logger_name)))
    return logging.getLogger(logging_key)


def set_app_logger(app: web.Application, app_config: AppConfig):
    logging.basicConfig(
        level=app_config.LOGGING_LEVEL,
        handlers=[logging.StreamHandler()],
        format="%(asctime)s.%(msecs)03d %(levelname)s: "
        "(%(filename)s:%(lineno)s): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app.logger = get_app_logger(app)
