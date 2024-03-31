from typing import Annotated

from fastapi import Depends, Request

from .handler import ChartHandler


async def _get_app_state(request: Request) -> ChartHandler:
    return request.app.state.chart_handler


AppState = Annotated[ChartHandler, Depends(_get_app_state)]
