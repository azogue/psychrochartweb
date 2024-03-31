import pytest

from psychrochartweb.pschart.chart_config import ChartCustomConfig
from tests.conftest import TEST_CONFIGS_PATH


@pytest.mark.parametrize(
    "path_config, valid",
    (
        ("default_ha.yaml", True),
        ("test_ha_sensors.yaml", True),
        ("ha_conf_2.yaml", True),
        ("bad_ha_conf_1.yaml", False),
        ("empty_ha_conf.yaml", False),
    ),
)
def test_parse_config(path_config: str, valid: bool) -> None:
    p = TEST_CONFIGS_PATH / path_config
    if not valid:
        with pytest.raises(ValueError):
            _config = ChartCustomConfig.from_yaml_file(p)
    else:
        _config = ChartCustomConfig.from_yaml_file(p)
