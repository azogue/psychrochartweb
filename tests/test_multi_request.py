import asyncio
import logging
from time import monotonic

from httpx import AsyncClient

from psychrochartweb.pschart.chart_config import ChartCustomConfig
from tests.conftest import PATH_FIXTURES

_URL_GET_SETTINGS = "/settings"
_URL_GET_CHART_CONFIG = "/chart-config"
_URL_GET_CHART = "/chart.svg"


async def _get_svg_response(client: AsyncClient):
    response = await client.get(_URL_GET_CHART)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    svg_data = response.content.decode()
    return svg_data


async def test_multi(caplog, local_client: AsyncClient):
    num_r = 30
    tasks = [_get_svg_response(local_client) for _ in range(num_r)]
    tic = monotonic()
    svg_r = await asyncio.gather(*tasks)
    toc = monotonic()
    logging.info(f"Multi req[{num_r}] took {toc - tic:.3f} s")
    for resp in svg_r[1:]:
        assert resp == svg_r[0]

    response = await local_client.get(_URL_GET_CHART_CONFIG)
    assert response.status_code == 200
    chart_config = ChartCustomConfig.model_validate(response.json())

    sleep_duration = chart_config.homeassistant.scan_interval + 0.05
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        for _ in range(2):
            logging.warning(
                f"Sleeping {sleep_duration} s to wait for chart rebuild"
            )
            await asyncio.sleep(sleep_duration)

            tasks = [_get_svg_response(local_client) for _ in range(num_r)]
            results = await asyncio.gather(*tasks)
            assert results[0] != svg_r[0]

        assert len(caplog.messages) == 0, caplog.messages

    svg_chart = await _get_svg_response(local_client)
    (PATH_FIXTURES / "test_chart_arrows.svg").write_text(svg_chart)
