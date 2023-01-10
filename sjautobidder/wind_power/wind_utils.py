# -*- coding: utf-8 -*-
"""Utility functions for calculating predicted wind turbine power output.

@author: Ben Page, Jacob Elford
"""

import os
import pickle as p
from typing import Union
from pathlib import Path

import numpy as np
import pandas as pd

from sjautobidder.met_office_api.api_interpolation import get_forecast


def get_wind_speed(forecast: pd.DataFrame) -> pd.DataFrame:
    """Unpacks wind speed from forecast.

     Unpacks wind speed in mph from a pd.DataFrame containing forecast data and
     converts it to m/s.

     Args:
        forecast (pd.DataFrame) : MetOffice forecast data.

    Returns:
        pd.DataFrame object containing wind speed and datetime information.
    """
    assert isinstance(forecast, pd.DataFrame)

    data = forecast[["DateTime", "S"]]

    data.loc[:, "S"] *= 0.44704  # mph to m/s conversion factor

    return data


def get_wind_power(windspeed: Union[list, np.ndarray, pd.Series, float],
                   height: Union[int, float] = 10) -> np.ndarray:
    """Converts windspeed to power.

     Converts a windspeed or set of windspeeds at a given height to power
     generated in kW according to the wind model created from the turbine
     datasheets.

     Args:
        windspeed (list, np.ndarray, float  : Windspeed or set of
                   pd.Series)                 windspeeds in m/s.
        height (int, float)                 : Rotor height (default is 10m)

    Returns:
        np.ndarray object corresponding to the power generated (in kW).

    Raises:
        ValueError  : if windspeed < 0
        ValueError  : if height < 0
    """

    n_turbines = 6  # Number of active turbines

    model_path = Path(__file__).absolute().parent / "model.p"
    hellman_exp = 0.34  # Hellman exponent for static air above inhabited areas
    assert os.path.isfile(model_path)  # Assert model exists
    assert isinstance(windspeed, (list, np.ndarray, float, pd.Series))
    assert isinstance(height, (int, float))

    if isinstance(windspeed, (list, float, pd.Series)):
        windspeed = np.asarray(windspeed)
    assert np.all(windspeed >= 0)  # Check all windspeeds are non-negative
    assert height >= 0

    correction = (height / 10)**hellman_exp  # Terrain/height correction

    with open(model_path, 'rb') as file:  # Load model from pickle
        model = p.load(file)

    windspeed *= correction
    windspeed[windspeed >= 30] = 30  # Truncate excess speeds
    return n_turbines * model(windspeed)


def get_wind_prediction():
    """Wrapper function to return array of predicted wind power generation for forecast timesteps.

    Returns:
        wind_report (pd.DataFrame): The wind speed and predicted wind energy output of wind turbines over the 
    next 24 hours, in 30 minute intervals (48 instances).
    """
    ALTITUDE = 250.0  # m above sea level
    forecast = get_forecast()
    wind_speed = get_wind_speed(forecast)
    wind_power = get_wind_power(wind_speed["S"], ALTITUDE)
    wind_report = pd.DataFrame(data={"DateTime": wind_speed["DateTime"], "WindSpeed": wind_speed["S"], "WindPower": wind_power})
    return wind_report
