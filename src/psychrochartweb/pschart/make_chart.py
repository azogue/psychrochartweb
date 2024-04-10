# -*- coding: utf-8 -*-
from io import BytesIO
from typing import Any

from psychrochart import load_config, PsychroChart


async def _save_chart_to_svg(chart: PsychroChart) -> bytes:
    bytes_svg = BytesIO()
    chart.save(bytes_svg, format="svg")
    bytes_svg.seek(0)
    raw = bytes_svg.read().decode()
    start = raw.find("<svg")
    assert start >= 0
    return raw[start:].encode()


async def plot_chart(
    rg_dbt: tuple[float, float],
    rg_w: tuple[float, float],
    pressure: float,
    points: dict[str, Any] | None = None,
    zones: list[Any] | None = None,
    arrows: dict[str, Any] | None = None,
    age: float = 0.0,
) -> bytes:
    c_conf = load_config("minimal")
    # c_conf.figure.figsize = [12, 8]
    c_conf.figure.x_label = None
    c_conf.figure.y_label = None
    c_conf.limits.pressure_kpa = pressure / 1000.0
    c_conf.limits.range_temp_c = rg_dbt
    c_conf.limits.range_humidity_g_kg = rg_w
    c_conf.chart_params.constant_rh_label = None
    c_conf.chart_params.constant_rh_curves = [20, 40, 50, 60, 80]
    c_conf.chart_params.with_constant_h = False
    c_conf.chart_params.constant_v_label = None
    c_conf.chart_params.constant_v_step = 0.02
    c_conf.chart_params.constant_temp_label = None
    c_conf.chart_params.constant_temp_step = 1
    c_conf.chart_params.constant_temp_label_step = 2
    c_conf.chart_params.with_constant_humidity = True
    c_conf.chart_params.constant_humid_label = None
    c_conf.chart_params.constant_humid_step = 2.5
    c_conf.chart_params.constant_humid_label_step = 2.5
    c_conf.chart_params.constant_wet_temp_label = None

    wet_temp_min = max(rg_dbt[0] - 5, c_conf.chart_params.range_wet_temp[0])
    c_conf.chart_params.range_wet_temp = (wet_temp_min, rg_dbt[1] - 3)

    # Make chart
    chart: PsychroChart = PsychroChart.create(c_conf)

    # TODO add custom zones from config
    chart.append_zones(
        {
            "zones": [
                {
                    "label": "Summer",
                    "points_x": [23, 28],
                    "points_y": [40, 60],
                    "style": {
                        "edgecolor": [1.0, 0.749, 0.0, 0.8],
                        "facecolor": [1.0, 0.749, 0.0, 0.2],
                        "linestyle": "--",
                        "linewidth": 2,
                    },
                    "zone_type": "dbt-rh",
                },
                {
                    "label": "Winter",
                    "points_x": [18, 23],
                    "points_y": [35, 55],
                    "style": {
                        "edgecolor": [0.498, 0.624, 0.8],
                        "facecolor": [0.498, 0.624, 1.0, 0.2],
                        "linestyle": "--",
                        "linewidth": 2,
                    },
                    "zone_type": "dbt-rh",
                },
            ]
        }
    )

    # TODO Customize lines, zones, etc.
    # Append lines
    t_min, t_opt, t_max = 16, 23, 30
    if rg_dbt[0] < t_min:
        chart.plot_vertical_dry_bulb_temp_line(
            t_min,
            {"color": [0.0, 0.125, 0.376], "lw": 2, "ls": ":"},
            f" TOO COLD, {t_min:g}°C",
            ha="left",
            loc=0.0,
            fontsize=14,
        )
    if rg_dbt[0] < t_opt < rg_dbt[1]:
        chart.plot_vertical_dry_bulb_temp_line(
            t_opt, {"color": [0.475, 0.612, 0.075], "lw": 2, "ls": ":"}
        )
    if rg_dbt[1] > t_max:
        chart.plot_vertical_dry_bulb_temp_line(
            t_max,
            {"color": [1.0, 0.0, 0.247], "lw": 2, "ls": ":"},
            f"TOO HOT, {t_max:g}°C ",
            ha="right",
            loc=1,
            reverse=True,
            fontsize=14,
        )

    if arrows:
        chart.plot_arrows_dbt_rh(arrows)
        # Append history label
        chart.axes.annotate(
            f"∆T:{age / 3600.0:.1f}h",
            (0, 0),
            xycoords="axes fraction",
            ha="left",
            va="bottom",
            fontsize=10,
            color="darkgrey",
        )

    if points:
        chart.plot_points_dbt_rh(points, convex_groups=zones)
        chart.plot_legend(
            frameon=False, fontsize=15, labelspacing=0.8, markerscale=0.8
        )

    # Append pressure / altitude label
    p_label = f"P={pressure / 100.0:.1f} mb "
    chart.axes.annotate(
        p_label,
        (1, 0.05),
        xycoords="axes fraction",
        ha="right",
        va="bottom",
        fontsize=15,
        color="darkviolet",
    )
    bytes_svg_data = await _save_chart_to_svg(chart)
    return bytes_svg_data
