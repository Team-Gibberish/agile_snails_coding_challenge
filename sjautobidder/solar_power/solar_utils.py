# -*- coding: utf-8 -*-
"""Utility functions for calculating predicted solar panel power output.

@author: MattSelwood
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pvlib as pv
from scipy.integrate import quad
from scipy.interpolate import interp1d


@dataclass
class SolarArray():
    """Class to represent a solar panel array.

    Attributes:
        area (float): Total solar array area in m^2.
        tilt (float): Angle in degrees that panels are inclined facing South.
        base_eff (float): Baseline efficiency of solar panels in array.
        pmpp (float): Temperature coefficient of panels in % per degree celsius.
        pmax (float): Maximum total output of solar array in Watts.

    """
    array_area: float
    panel_tilt: float
    base_efficiency: float
    temperature_coeff: float
    max_output: float


def load_forecast(file_path: str) -> pd.DataFrame:
    """Loads json API forecast as pandas DataFrame.

    Args:
        file_path (str): File path pointing to a forcast json file.

    Returns:
        pd.DataFrame: A dataframe constructed from the json file.
    """
    forecast = pd.DataFrame(pd.read_json(file_path, orient="columns", convert_dates=True))
    return forecast


def temperature_efficiency(
    base_eff: float, temp_coef: float, forecast: pd.DataFrame
) -> float:
    """Function to calculate the effective panel efficiency at a particular temperature.

    Args:
        base_eff (float): Base efficiency.
        temp_coef (float): Temperature coefficient in % per degree celsius.
        forecast (pd.DataFrame): Forcast DataFrame.

    Returns:
        float: solar panel efficiency at the given temperature.
    """
    temperature = forecast["T"]
    temperature_diff = temperature - 25
    eff_change = temperature_diff * temp_coef
    return base_eff + eff_change


def weather_factor(forecast: pd.DataFrame) -> pd.Series:
    """Returns the weather efficiency factor for the forcast.

    Returns weather factor efficiency multiplier based on MetOffice API
    weather type for a one hour timestep.

    Args:
        forecast (pd.DataFrame): Forcast dataframe.

    Returns:
        pd.Series: Weather efficiency factor for the provided forcast.
    """
    weather = forecast["W"]
    weather_list = []
    no_change = [0, 1]
    med_change = [2, 3, 5, 8]
    heavy_change = [6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 28, 29, 30]
    largest_change = [19, 20, 21, 22, 23, 24, 25, 26, 27, 4]
    for wtype in weather:
        if wtype in no_change:
            weather_list.append(1.0)
        if wtype in med_change:
            weather_list.append(0.5)
        if wtype in heavy_change:
            weather_list.append(0.1)
        elif wtype in largest_change:
            weather_list.append(0.0)
    return pd.Series(weather_list)


def get_incident_power(
    forecast: pd.DataFrame, location: pv.location.Location, tilt: float, area: float
) -> pd.Series:
    """Returns the clear-sky power incident on solar panel array.

    Returns clear-sky power from Sun incident on a solar panel array of a
    given area and tilt (South facing) at a given location for the times
    provided by MetOffice API forecast output.

    Args:
        forecast (pd.DataFrame): Forcast dataframe.
        location (pv.location.Location): Location of solar array.
        tilt (float): Angle in degrees that panels are inclined facing South.
        area (float): Total solar array area in m^2.

    Returns:
        pd.Series: Clear-sky power incident on solar array for each forecast timestep.
    """
    times = pd.DatetimeIndex(
        forecast["DateTime"]
    )  # define times to model sun position / insolation from
    solar_pos = location.get_solarposition(
        times
    )  # calculate solar position at defined location on defined times
    clearsky = location.get_clearsky(
        times
    )  # calculate insolation at location for date range
    ghi = clearsky.ghi  # calculate insolation incident on tilted solar panel
    flux_density = (
        ghi * np.sin(np.deg2rad(solar_pos["apparent_elevation"]) + np.deg2rad(tilt))
    ) / np.sin(np.deg2rad(solar_pos["apparent_elevation"]))
    power_incident = flux_density * area  # Watts #calculate power of whole array
    return power_incident


def get_total_efficiency(
    forecast: pd.DataFrame, base_eff: float, pmpp: float
) -> pd.Series:
    """Returns total efficiency of Solar panels for each forecast step.

    Returns the total efficiency of Solar panels for each forecast time step
    depending on temperature and weather condition factors.

    Args:
        forecast (pd.DataFrame): Forcast dataframe.
        base_eff (float): Baseline efficiency of solar panels.
        pmpp (float): Temperature coefficient of solar panels (% per degree Celsius).

    Returns:
        pd.series: Total Solar panel efficiency at each forecast timestep.
    """
    times = pd.DatetimeIndex(forecast["DateTime"])
    efficiency_temperature_mod = temperature_efficiency(
        base_eff, pmpp, forecast
    )  # effiency change from temperature
    weather = weather_factor(forecast)  # weather factor efficency multiplier
    total_eff = efficiency_temperature_mod * np.asarray(weather)  # total efficiency
    total_eff.index = times  # change index to datetimes consistent with forecast
    return total_eff


def get_generated_power(
    incident_power: pd.Series,
    total_efficiency: pd.Series,
    datetimes: pd.DatetimeIndex,
    max_array_output: float,
) -> pd.Series:
    """Returns net generated power of solar array from incident power and panel
    efficiency.

    Returns a series object containing the solar array predicted output for each
    timestep from an incident power series object and a panel efficiency series in
    Watts.

    Args:
        incident_power (pd.Series): Clear-sky power incident on solar array for each
        forecast timestep.
        total_efficiency(pd.Series): Total Solar panel efficiency at each forecast
        timestep.
        datetimes (pd.DatetimeIndex): Array of Datetimes corresponding to the start
        of each forecast timestep.
        max_array_output (float): Maximum total output of solar array in Watts.

    Returns:
        pd.Series: Predicted solar array output for each timestep of forecast in Watts.
    """
    output_power = incident_power * total_efficiency  # Watts
    output_power[
        output_power > max_array_output
    ] = max_array_output  # cap power output at max power output of array
    hours_since_23 = np.linspace(0, 24, 49)
    power_curve = interp1d(
        hours_since_23, output_power
    )  # interpolate power into function of time
    generated_power = []
    for i in range(len(hours_since_23) - 1):
        lower_limit = hours_since_23[i]
        upper_limit = hours_since_23[i + 1]
        integral = quad(
            power_curve, lower_limit, upper_limit
        )  # integrate hourly intervals
        generated_power.append(integral[0])  # Watts/hr
    generated_power.append(0.0)  # 23:00 - 00:00 interval needs a value for array shapes
    # generated_power = np.asarray(generated_power) / 1000 #convert to kW/hr
    generated_power_series = pd.Series(generated_power)
    generated_power_series.index = datetimes
    return generated_power_series


def predict_solar(
    forecast: pd.DataFrame, location: pv.location.Location, solar_array: SolarArray
) -> pd.Series:
    """Returns predicted solar array output for a given forecast, location and solar
    array parameters.

    Wrapper function that returns predicted solar array output for each timestep of
    a given forecast at a defined location and for a set of solar array parameters.

    Args:
        forecast (pd.DataFrame): Forcast dataframe.
        location (pv.location.Location): Location object of solar array.
        solar_array (SolarArray): Object describing solar array properties.

    Returns:
        pd.Series: Predicted solar array output for each timestep of forecast in Watts.
    """
    forecast_datetimes = pd.DatetimeIndex(
        forecast["DateTime"]
    )  # create array of forecast step DatetimeIndicies
    power_incident = get_incident_power(
        forecast, location, solar_array.panel_tilt, solar_array.array_area
    )  # calculate power incident on array
    total_efficiency = get_total_efficiency(
        forecast, solar_array.base_efficiency, solar_array.temperature_coeff
    )  # calculate total efficiency based on temp and weather conditions
    power_generated = get_generated_power(
        power_incident, total_efficiency, forecast_datetimes, solar_array.max_output
    )  # calculate the power generated by the solar array for each forecast timestep
    return power_generated
