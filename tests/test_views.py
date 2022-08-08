import logging

import pytest
from aiohttp.client_reqrep import ClientResponse

from psychrochartweb.routes import ENDPOINT_CHART_SVG
from tests.conftest import TEST_PATH


async def _get_chart(client, svg_name: str):
    get_response: ClientResponse = await client.get(ENDPOINT_CHART_SVG)
    assert get_response.status == 200
    logging.info(get_response.headers)
    assert get_response.headers["Content-Type"] == "image/svg+xml"
    text_response = await get_response.read()
    logging.info(text_response[:100])
    with open(TEST_PATH / svg_name, mode="wb") as f:
        f.write(text_response)


@pytest.mark.asyncio
async def test_get_empty_chart(client):
    await _get_chart(client, "test_empty_chart.svg")


@pytest.mark.local_access
@pytest.mark.asyncio
async def test_get_chart(local_client):
    await _get_chart(local_client, "test_chart.svg")
