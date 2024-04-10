import logging

from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from psychrochartweb.config import Settings
from psychrochartweb.handler import ChartHandler
from psychrochartweb.pschart.chart_config import ChartCustomConfig
from tests.conftest import PATH_FIXTURES

_URL_GET_APP_STATE = "/"
_URL_GET_APP_SETTINGS = "/settings"
_URL_GET_CHART_CONFIG = "/chart-config"
_URL_GET_CHART = "/chart.svg"


async def _get_chart(client: AsyncClient, svg_name: str) -> str:
    response = await client.get(_URL_GET_CHART)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    text_response = response.content.decode()
    logging.info(text_response[:100])
    (PATH_FIXTURES / svg_name).write_text(text_response)
    return text_response


async def test_get_empty_chart(client: AsyncClient):
    svg_chart = await _get_chart(client, "test_empty_chart.svg")

    response = await client.get(_URL_GET_APP_STATE)
    assert response.status_code == 200
    state = ChartHandler.model_validate_json(response.content)
    assert state.current_svg_chart
    assert state.current_svg_chart.decode() == svg_chart

    response = await client.get(_URL_GET_APP_SETTINGS)
    assert response.status_code == 200
    settings = Settings.model_validate_json(response.content)
    assert not settings.ha_config_name

    response = await client.get(_URL_GET_CHART_CONFIG)
    assert response.status_code == 200
    chart_config = ChartCustomConfig.model_validate_json(response.content)
    assert not chart_config.exterior
    assert not chart_config.interior
    assert not chart_config.ha_sensors
    assert chart_config.interior_style_line
    assert chart_config.interior_style_fill
    assert chart_config.exterior_style_line
    assert chart_config.exterior_style_fill
    assert chart_config.homeassistant.host


async def test_get_chart(httpx_mock: HTTPXMock, local_client: AsyncClient):
    _svg_chart = await _get_chart(local_client, "test_chart_filled.svg")

    response = await local_client.get(_URL_GET_CHART_CONFIG)
    assert response.status_code == 200
    chart_config = ChartCustomConfig.model_validate_json(response.content)
    assert chart_config.ha_sensors
    assert chart_config.homeassistant.host

    assert len(httpx_mock.get_requests()) == 1


async def test_real_chart_data(local_client: AsyncClient):
    _svg_chart = await _get_chart(local_client, "test_chart.svg")

    response = await local_client.get(_URL_GET_CHART_CONFIG)
    assert response.status_code == 200
    chart_config = ChartCustomConfig.model_validate_json(response.content)
    assert chart_config.ha_sensors
    assert chart_config.homeassistant.host
