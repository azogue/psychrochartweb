import pathlib

import httpx
import pytest
import pytest_asyncio
from pytest_httpx import HTTPXMock

from psychrochartweb.app import create_app
from psychrochartweb.config import Settings
from psychrochartweb.handler import ChartHandler

_TEST_PATH = pathlib.Path(__file__).parent
TEST_CONFIGS_PATH = _TEST_PATH / "custom_configs"
PATH_FIXTURES = _TEST_PATH / "fixtures"

TEST_SETTINGS = Settings(ha_config_name="", custom_folder=TEST_CONFIGS_PATH)
TEST_LOCAL_SETTINGS = Settings(
    ha_config_name="test_ha_sensors.yaml", custom_folder=TEST_CONFIGS_PATH
)


async def make_device_testclient(hostname: str, settings: Settings):
    """Async generator to produce TestClient with setup/shutdown stages."""
    app = create_app(settings)

    chart_handler = ChartHandler.create(settings)
    await chart_handler.start()
    app.state.chart_handler = chart_handler
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=f"http://{hostname}"
    ) as tc:
        yield tc
    await chart_handler.stop()


@pytest_asyncio.fixture
async def client():
    async for tc in make_device_testclient("test-server", TEST_SETTINGS):
        yield tc


@pytest_asyncio.fixture
async def local_client(httpx_mock: HTTPXMock):
    fake_ha_url = "http://192.168.1.111:8123/api/states"
    num_reqs = {"count": 0}

    async def _mock_get_ha_states(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == fake_ha_url
        assert request.headers["Authorization"] == "Bearer super-secret"
        num_reqs["count"] += 1
        assert num_reqs["count"] < 4
        mock_states = f"ha-sensor-data-{num_reqs['count']}.json"
        return httpx.Response(
            status_code=200,
            content=(PATH_FIXTURES / mock_states).read_bytes(),
        )

    httpx_mock.add_callback(_mock_get_ha_states, url=fake_ha_url, method="GET")
    async for tc in make_device_testclient(
        "test-local-server", TEST_LOCAL_SETTINGS
    ):
        yield tc


@pytest.fixture
def non_mocked_hosts() -> list[str]:
    return ["test-local-server", "test-server"]
