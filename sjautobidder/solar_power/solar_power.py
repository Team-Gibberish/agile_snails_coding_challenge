#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to read in interpolated API forecast as command line argument and output hourly
solar power production predictions

@author: MattSelwood
"""

import pvlib as pv
import pandas as pd

from sjautobidder.solar_power.solar_utils import SolarArray
from sjautobidder.solar_power.solar_utils import predict_solar
from sjautobidder.met_office_api.api_interpolation import get_forecast

def get_solar_prediction() -> pd.Series:
    """Get the predicted Solar Panel output. 
    
    Returns the predicted solar array output in W for next 23:00 - 23:00 interval, 
    in 30 min steps.
    
    Returns: pd.Series: The predicted solar energy output of solar array over the 
    next 24 hours, in 30 minute intervals (48 instances).
    """
    # set panel / location parameters
    TIMEZONE = "Europe/London"
    LATITUDE = 52.1051
    LONGITUDE = -3.6680
    ALTITUDE = 250.0  # m above sea level
    PANEL_TILT = 45.0  # angle panels are tilted at (south facing)
    ARRAY_AREA = 50.0 * 50.0  # area covered by array in m^2
    BASE_EFFICIENCY = 0.196  # base efficiency of panels
    PMPP = -0.0037  # %/C
    PMAX_ARRAY = 469_000  # W
    
    forecast = get_forecast() # get forecast from MetOffice API
    aimlac_location = pv.location.Location(
        LATITUDE, LONGITUDE, tz=TIMEZONE, altitude=ALTITUDE
    )  # define location of solar panel installation
    aimlac_solar_array = SolarArray(
        ARRAY_AREA, PANEL_TILT, BASE_EFFICIENCY, PMPP, PMAX_ARRAY
    )  # create SolarArray object to describe aimlacHQ solar panel array
    predicted_solar_output = predict_solar(
        forecast, aimlac_location, aimlac_solar_array
    )  # calculate predicted solar output from forecast, location and array parameters
    predicted_solar_output /= 1000. # convert to kW
    return predicted_solar_output
