from fastapi import APIRouter, Response

from .config import Settings
from .dependencies import AppState
from .handler import ChartHandler
from .pschart.chart_config import ChartCustomConfig


class SVGResponse(Response):
    media_type = "image/svg+xml"


router = APIRouter()


@router.get("/", response_model=ChartHandler)
def _app_state(handler: AppState):
    return handler


@router.get("/settings", response_model=Settings)
def _app_settings(handler: AppState):
    return handler.settings


@router.get("/chart-config", response_model=ChartCustomConfig)
def _chart_config(handler: AppState):
    return handler.ha_config


@router.get("/chart.svg", response_class=SVGResponse)
def _current_chart(handler: AppState):
    assert handler.current_svg_chart is not None
    return SVGResponse(content=handler.current_svg_chart)
