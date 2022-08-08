import pathlib

import pytest
from aiohttp.test_utils import TestClient

from psychrochartweb.app import AppConfig, create_app

TEST_PATH = pathlib.Path(__file__).parent
TEST_CONFIGS_PATH = TEST_PATH / "custom_configs"


@pytest.fixture
def client(aiohttp_client, event_loop) -> TestClient:
    app_config = AppConfig()
    assert app_config.SCAN_INTERVAL is None
    app_config.SCAN_INTERVAL = 1
    app_config.CUSTOM_FOLDER = TEST_CONFIGS_PATH
    app_config.HA_CONFIG_NAME = ""
    app = create_app(name="pschart_test", config=app_config)
    return event_loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
def local_client(aiohttp_client, event_loop) -> TestClient:
    app_config = AppConfig()
    assert app_config.SCAN_INTERVAL is None
    app_config.SCAN_INTERVAL = 1
    app_config.HA_CONFIG_NAME = "my_ha_sensors.yaml"
    app = create_app(name="pschart_test_ha", config=app_config)
    return event_loop.run_until_complete(aiohttp_client(app))
