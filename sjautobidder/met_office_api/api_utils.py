# -*- coding: utf-8 -*-
"""Functions to collect and interpolate MetOffice's API data.

Functions to collect and interpolate MetOffice's API 3-hourly forecast into 1
hour intervals.

@author: MattSelwood
"""

from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from requests import Response

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def datetime_array(response: Response, hours: int, step: int) -> List[str]:
    """Get an array of datetime strings for the number of hours in step increments.

    Returns an array of strings in the datetime format ``2021-05-05T13: 00: 00Z``
    from the forecast start time for a defined amount of hours in a defined step
    size (in hours). Total hours must be an exact multiple of step size.

    Args:
        response (Response): The json response from a met office API to obtain
            the initial datetime.
        hours (int): The total number of hours covered by result array. Must be
            an exact multiple of step size.
        step (int): The step size between each hour.

    Returns: List[str]: A list of strings in the datetime format
        ``2021-05-05T13: 00: 00Z``
    """
    assert hours % step == 0  # make sure hours is increment of 3

    start_datetime = datetime.strptime(
        response.json()["SiteRep"]["DV"]["dataDate"], DATETIME_FORMAT
    )
    intervals = []
    for i in range((hours // step) + 1):
        tstep = start_datetime + relativedelta(hours=+(i * 3))
        intervals.append(tstep)
    dts = [dt.strftime(DATETIME_FORMAT) for dt in intervals]
    return dts


def count_forecasts(response: Response) -> int:
    """Returns the total number of forecasts in an API response.

    Args:
        response (Response): The json response from a met office API

    Returns:
        int: The number of forecasts in the response.
    """
    # object containing forecasts
    period = response.json()["SiteRep"]["DV"]["Location"]["Period"]
    counts = 0
    for forecast in period:
        counts += len(forecast["Rep"])
    return counts


def forecast_times_no24(response: Response) -> List[int]:
    """Obtain the cumulative time passed from each forcast response.

    Start times of each individual forecast in API response returned as
    cumulative hours from start hour (for finding first 23:00 instance)

    Args:
        response (Response): The json response from a met office API.

    Returns:
        List[int]: Cumulative hours passed from the starting hour.
    """
    start_datetime = datetime.strptime(
        response.json()["SiteRep"]["DV"]["dataDate"], DATETIME_FORMAT
    )
    start = start_datetime.hour
    num = count_forecasts(response)
    times = []
    for i in range(num + 1):
        times.append(start + (i * 3))
    return times


def unpack_forecasts(response: Response) -> List[dict]:
    """Unpacks all forecasts from API response into a list of dictionaries.

    Args:
        response (Response): The json response from a met office API.

    Returns:
        List[dict]: A list of forcasts unpacked from an API response.
    """
    period = response.json()["SiteRep"]["DV"]["Location"]["Period"]
    forecasts = []
    for forecast in period:
        for instance in forecast["Rep"]:
            forecasts.append(instance)
    return forecasts


def elevens(response: Response) -> Tuple[List[dict], List[str]]:
    """Fetches forecast and datetime stamps for next 23:00 to 23:00 interval.

    Fetches forecast and datetime stamps for next 23:00 to 23:00 interval and
    returns them as lists.

    Args:
        response (Response): The json response from a met office API.

    Returns: Tuple[List[dict], List[str]]: A list of forcasts and their
        corresponding attributes, along with a list of timestamps of each
        forcast.
    """
    cum_hrs = forecast_times_no24(response)
    dts = np.array(datetime_array(response, 60, 3))
    forecasts = np.array(unpack_forecasts(response))
    if 23 in cum_hrs:
        start_idx = np.where(np.asarray(cum_hrs) == 23)[0][0]
    else:
        start_idx = np.where(np.array(cum_hrs) > 23)[0][0] - 1
    end_idx = start_idx + 10  # cover entire 24 hour range
    idxs = np.arange(start_idx, end_idx + 1)
    return list(forecasts[idxs]), list(dts[idxs])


def interp_30min(response) -> pd.DataFrame:
    """Interpolates 3-hourly weather report into 30-min intervals.

    Interpolates 3-hourly weather report into 30-min intervals and attaches
    corresponding DateTime stamps. Forecast between 23:00-23:00 returned as a
    Pandas DataFrame

    Args: response (Response): The json response from a met office API.

    Returns: pd.DataFrame: A dataframe containing the forcast variables along
        with datetimes across a 23:00 - 23:00 timespan in 30 minute interpreted
        increments.
    """
    # Obtain forecasts and their datetimes
    forecasts, datetimes = elevens(response)

    # Create DataFrame
    dataframe = pd.DataFrame(
        columns={
            "D": [],
            "F": [],
            "G": [],
            "H": [],
            "Pp": [],
            "S": [],
            "T": [],
            "V": [],
            "W": [],
            "U": [],
            "$": [],
            "DateTime": [],
        }
    )

    # Loop through all but the last forecast
    for i in range(len(forecasts) - 1):

        # Current forecast
        curr = forecasts[i]

        # Future forecast in 3 hours
        new = forecasts[i + 1]

        # Time slices between current and future forecast
        times = [0.5, 1, 1.5, 2, 2.5]

        # New datetimes
        t_curr = datetime.strptime(datetimes[i], DATETIME_FORMAT)
        curr["DateTime"] = t_curr.strftime(DATETIME_FORMAT)
        new["DateTime"] = datetimes[i + 1]

        # Append non-interpreted values
        dataframe = dataframe.append(curr, ignore_index=True)

        # For each time span, interpret results
        for k, time in enumerate(times):
            interp = {
                "DateTime": (t_curr + relativedelta(hours=time)).strftime(
                    DATETIME_FORMAT
                )
            }
            # For every variable in the forecast
            for key in list(forecasts[0].keys()):
                if key in ["F", "G", "H", "Pp", "S", "T", "$"]:
                    # Continuous interpolation
                    if new[key] >= curr[key]:
                        # New Value is greater
                        diff = abs(float(curr[key]) - float(new[key]))
                        val = float(curr[key]) + (diff * ((k + 1) / (len(times) + 1)))
                    else:
                        # New Value is smaller
                        diff = abs(float(curr[key]) - float(new[key]))
                        val = float(curr[key]) - (diff * ((k + 1) / (len(times) + 1)))
                    interp[key] = str(val)

                else:
                    # Discrete interpolation
                    if str(key) == "DateTime":
                        # Ignore the DateTime key as it is interpreted at the start
                        continue
                    # Assuming time slices are equidistant, use the closest forecast
                    interp[key] = curr[key] if k <= len(times) // 2 else new[key]

            # Add interpreted
            dataframe = dataframe.append(interp, ignore_index=True)

    # Cast to types
    dataframe = dataframe.astype(
        {
            "D": str,
            "F": float,
            "G": float,
            "H": float,
            "Pp": float,
            "S": float,
            "T": float,
            "V": str,
            "W": int,
            "U": int,
            "$": float,
            "DateTime": str,
        }
    )
    return dataframe


def cut_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Cut a dataframe on the DateTime column into intervals of 23:00 - 23:00.

    Cuts a given Pandas DataFrame via a string DateTime column into an interval
    of 23:00 - 23:00.

    Args:
        frame (pd.DataFrame): Pandas dataframe to be cut. Must contain a DataTime
            column.

    Returns: pd.DataFrame: Pandas dataframe cut into intervals of 23:00 - 23:00
    """
    hrs = []
    for i in range(len(frame["DateTime"])):
        hrs.append(datetime.strptime(frame["DateTime"][i], DATETIME_FORMAT).hour)
    idxs = np.where(np.asarray(hrs) == 23)[0]
    start = idxs[0]
    end = idxs[2]  # next 23 start will be 23:30 so need second item
    cut = frame.truncate(start, end)
    return cut


def interpolate_api_response(response: Response) -> pd.DataFrame:
    """Get hourly forcasts for the next 23:00 - 23:00 interval.

    Returns interpolated 1-hourly forecasts from a met office API response for
    the next 23:00 - 23:00 interval as a pandas dataframe.

    Args:
        response (Response): The json response from a met office API.

    Returns: pd.DataFrame: Hourly forcasts for the next 23:00 - 23:00 interval.
    """
    out = cut_frame(interp_30min(response))
    return out
