"""Tests for the solar power generation functions."""
import pandas as pd

from sjautobidder.solar_power.solar_utils import temperature_efficiency


def test_load_forecast():
    """Test to ensure a forcast is loaded correctly."""


def test_efficiency():
    """Test to ensure panel efficiency is calculated correctly."""
    test_forecast = pd.DataFrame([10], columns=["T"])
    test_temp_coeff = 0.9
    test_base_eff = 0.5

    result = temperature_efficiency(test_base_eff, test_temp_coeff, test_forecast)

    assert isinstance(result, float)
    assert result == -13.0


def test_weather_factor():
    """Test to ensure a weather factor is calculated correctly."""
