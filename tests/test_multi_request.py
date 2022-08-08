import asyncio
import logging
from time import monotonic

import pytest
from psychrochartweb.config import get_config
from psychrochartweb.routes import ENDPOINT_CHART_SVG


@pytest.mark.asyncio
async def _get_svg_response(client):
    r = await client.get(ENDPOINT_CHART_SVG)
    assert r.status == 200
    assert r.content_type == "image/svg+xml"
    svg_data = await r.read()
    return svg_data


@pytest.mark.asyncio
async def test_multi(client):
    num_r = 30
    tasks = [_get_svg_response(client) for _ in range(num_r)]
    tic = monotonic()
    svg_r = await asyncio.gather(*tasks)
    toc = monotonic()
    logging.info(f"Multi req[{num_r}] took {toc - tic:.3f} s")

    for resp in svg_r[1:]:
        assert resp == svg_r[0]

    sleep_duration = get_config(client.app).SCAN_INTERVAL + 0.5
    logging.warning(f"Sleeping {sleep_duration} s to wait for chart rebuild")
    await asyncio.sleep(sleep_duration)

    tasks = [_get_svg_response(client) for _ in range(num_r)]
    results = await asyncio.gather(*tasks)
    assert results[0] != svg_r[0]
