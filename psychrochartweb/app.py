import asyncio
import logging
from contextlib import asynccontextmanager

import uvloop
from fastapi import FastAPI, Response

from .config import Settings
from .handler import ChartHandler
from .routes import router

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class SVGResponse(Response):
    media_type = "image/svg+xml"


def create_app(settings: Settings) -> FastAPI:
    """Instantiate main application."""

    @asynccontextmanager
    async def app_lifespan(app: FastAPI):  # pragma: no cover
        """App lifespan"""
        chart_handler = ChartHandler.create(settings)
        await chart_handler.start()
        app.state.chart_handler = chart_handler
        try:
            yield
        except asyncio.CancelledError:
            logging.warning("Bad app exit (open connections)")
        await chart_handler.stop()

    application = FastAPI(
        title="Psychrochart-web",
        version=settings.version,
        lifespan=app_lifespan,
    )
    application.include_router(router)
    return application


app_settings = Settings()
app = create_app(app_settings)
logging.basicConfig(
    level=app_settings.app_log_level,
    handlers=[logging.StreamHandler()],
    format="%(asctime)s.%(msecs)03d %(levelname)s: "
    "(%(filename)s:%(lineno)s): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
