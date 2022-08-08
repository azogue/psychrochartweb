# -*- coding: utf-8 -*-
from aiohttp import web

from .config import SVG_BYTES


class ChartView(web.View):
    """View to get the chart."""

    async def get(self):
        """Simple GET to access the SVG chart data."""
        chart_svg_b = self.request.app[SVG_BYTES]

        return web.Response(body=chart_svg_b, content_type="image/svg+xml",)
