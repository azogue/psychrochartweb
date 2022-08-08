# import pytest
# from tests.conftest import TEST_CONFIGS_PATH
#
# from psychrochartweb.pschart import ChartCustomConfig
#
#
# @pytest.mark.parametrize(
#     "path_config",
#     (
#         "default_ha.yaml",
#         "my_ha_sensors.yaml",
#         "bad_ha_conf_1.yaml",
#         "empty_ha_conf.yaml",
#         "ha_conf_2.yaml",
#         # "nonexistent.yaml",
#     ),
# )
# def test_get_chart(path_config):
#     p = TEST_CONFIGS_PATH / path_config
#     _config = ChartCustomConfig.from_yaml_file(p)
