# -*- coding: utf-8 -*-
"""URL routing file for the base app."""
from aiohttp import web

from .views import ChartView

ENDPOINT_CHART_SVG = "/chart_svg"

routes = [
    web.view(ENDPOINT_CHART_SVG, ChartView),
]
