"""Tests for the solar power generation functions."""
import pytest
import pandas as pd
import numpy as np
import pvlib as pv

from sjautobidder.solar_power.solar_utils import (
        load_forecast,
        temperature_efficiency,
        weather_factor,
        get_incident_power,
        get_total_efficiency,
        get_generated_power,
        predict_solar,
        SolarArray,
)

from sjautobidder.solar_power.solar_power import get_solar_prediction

from sjautobidder.autobidder.autobidder_utils import get_forecast

def test_load_forecast():
    """Test to ensure a forcast is loaded correctly."""


def test_efficiency():
    """Test to ensure panel efficiency is calculated correctly."""
    test_forecast = pd.DataFrame([10], columns=["T"])
    test_temp_coeff = 0.9
    test_base_eff = 0.5

    result = temperature_efficiency(test_base_eff, test_temp_coeff, test_forecast)

    assert result.dtype == np.float64
    assert result.item() == -13.0


@pytest.mark.parametrize(
    "weather_change, expect",
    [(0,1.),(2,.5),(6,.1),(19,0.)],
    ids=["no_change", "med_change", "heavy_change", "largest_change"]
)
def test_weather_factor(weather_change, expect):
    """Test to ensure a weather factor is calculated correctly."""
    #test_forecast = get_forecast(date, period)
    #output = weather_factor(test_forecast)
    test_forecast = pd.DataFrame([weather_change], columns=["W"])
    result = weather_factor(test_forecast)

    assert isinstance(result, pd.Series)
    assert result.dtype == float
    assert result.item() == pytest.approx(expect,1e-2)

def test_get_incident_power():
    """Test to ensure incident power is calculated correctly."""
    test_forecast = pd.DataFrame(["2023-09-18"], columns=["DateTime"])
    lat = 51.6214
    lon = -3.9436
    loc = pv.location.Location(lat, lon, name="Swansea")
    tilt = 0.5
    area = 100
    result = get_incident_power(test_forecast, loc, tilt, area)

    assert isinstance(result, pd.Series)
    assert result.dtype == float

def test_total_efficiency():
    """Test to ensure total efficiency is calculated correctly."""
    test_forecast = pd.DataFrame(["2023-09-18"], columns=["DateTime"])
    test_forecast["T"] = 10
    test_forecast["W"] = 0
    base_eff = 0.5
    pmpp = 50
    result = get_total_efficiency(test_forecast, base_eff, pmpp)

    assert isinstance(result, pd.Series)
    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.dtype == float

def test_get_generated_power():
    """Test to ensure generated power is calculated correctly."""
    incident_power = pd.Series(np.random.uniform(0,1,49))
    total_efficiency = pd.Series(np.random.uniform(0,1,49))
    test_date = pd.date_range("2023-09-18", periods=49, freq="H")
    max_array_output = 100
    
    result = get_generated_power(incident_power, total_efficiency, test_date, max_array_output)
    
    assert isinstance(result, pd.Series)
    assert len(result) == 49
    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.dtype == float


def test_predict_solar():
    """Test to ensure solar power prediction is calculated correctly."""
    test_date = pd.date_range("2023-09-18", periods=49, freq="H")
    test_forecast = pd.DataFrame(test_date, columns=["DateTime"])
    test_forecast["T"] = np.random.uniform(0,1,49)
    test_forecast["W"] = np.random.randint(0,31,49)

    lat = 51.6214
    lon = -3.9436
    loc = pv.location.Location(lat, lon, name="Swansea")
    solar_array = SolarArray(100, 0.5,0.5,0.9,100)

    result = predict_solar(test_forecast, loc, solar_array)

    assert isinstance(result, pd.Series)


# solar_power.py
def test_get_solar_prediction():
    result = get_solar_prediction()

    assert isinstance(result, pd.Series)
    assert result.dtype == float
    assert result.shape == (49,)

