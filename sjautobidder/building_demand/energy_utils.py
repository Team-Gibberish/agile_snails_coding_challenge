"""Various helper functions to calculate the energy demand of the building.

Todo:
    get_active_office_mask() Should account for bank holidays and Christmas.
"""

import datetime
import pandas as pd

from typing import List

from sjautobidder.met_office_api.api_interpolation import get_forecast


def get_next_24_hour_datetime(start_time: datetime.datetime) -> List[datetime.datetime]:
    """Get datetime objects for the next 24 hours.

    Returns an array of datetime objects of the next 24 hour interval, in 30
    minute steps.

    Args: start_time (datetime.datetime): Start time of the 24 hour
        period.

    Returns: List[datetime.datetime]: An array of datetime objects of the next
        24 hour interval in 30 minute steps from the given start time (48
        instances).
    """
    date_times = [start_time + datetime.timedelta(minutes=30*i) for i in range(48)]
    return date_times


def get_active_office_mask(start_time: datetime.datetime) -> List[bool]:
    """Returns a boolean array for office occupancy for the next 24 hours.

    Returns an array of booleans (True/False) of 30 minute intervals where True
    is when the office will be in use by staff.

    Args: start_time (datetime.datetime): Start time of the 24 hour
        period.

    Returns: List[bool]: An array of booleans of the next 24 hour period where
        True is when the office will be in use by staff.
    """
    # Define office start and end times
    day_start = datetime.time(9, 0, 0)
    day_end = datetime.time(17, 0, 0)

    # Generate mask with list comprehension and if clause
    mask = [day_start <= dt.time() <= day_end and dt.weekday() < 5 
            for dt in get_next_24_hour_datetime(start_time)]
    return mask


def temp_to_energy(temp: int) -> int:
    """Converts an outside temperature reading to a heating energy demand.

    Args:
        temp (int): Temperature of the outside reading in degrees celsius.

    Returns:
        int: amount of power used by the heating system in kilowatts.
    """
    if temp <= 0:
        return 120

    elif 0 < temp <= 5:
        return 90
    
    elif 5 < temp <= 10:
        return 60
    
    elif 10 < temp <= 15:
        return 30
    
    elif temp >= 15:
        return 0



def get_temperatures() -> List[int]:
    """Get the tempreture of the site for the next 24 hours.

    Get the temperature of the site for the next 24 hours in 30 minute
    intervals. Currently a dummy function.

    Returns: List[int]: The temperature in celsius of the site for the next 24
        hours in 30 minute intervals (48 instances).
    """
    forecast = get_forecast()
    temperatures = forecast["T"].to_numpy(dtype="float")
    if len(temperatures) == 49:
        temperatures = temperatures[:-1]
    return temperatures.tolist()


def create_initial_demand_dataframe(start_time: datetime.datetime) -> pd.DataFrame:
    """
    Creates the initial empty dataframe used when calculating the energy demand
    of the building.

    Args:
        start_time (datetime.datetime): Start time of the 24 hour period.

    Returns:
        pd.DataFrame: Each row is a time interval, in 30 minute periods, for the
                      next 11pm-11pm slot
    """

    times = []
    for i in range(48):
        new_time = start_time + datetime.timedelta(minutes=30 * i)
        times.append(new_time.strftime("%Y-%m-%dT%H:%M:%SZ"))

    active_office_mask = get_active_office_mask(start_time)

    data = {"DateTime": times, "Active office mask": active_office_mask}

    initial_data_frame = pd.DataFrame(data)
    initial_data_frame["Heating"] = 0
    initial_data_frame["Data Centre"] = 0
    initial_data_frame["Office Equipment"] = 0
    initial_data_frame["LightingOther"] = 0

    return initial_data_frame


def adjust_datetime(start_time: datetime.datetime):
    """Rounds up the datetime object to the next half hour period.

    If the time is between half hour periods xx:00 and xx:30, then it will 'round up'
    to the xx:30 slot, and vice versa.

    Args:
        start_time (datetime.datetime): Start time of the 24 hour period.

    Returns:
        adjusted_time (datetime.datetime): The time adjusted to the next half hour slot.
    """

    if start_time.minute % 30 != 0:
        start_time += datetime.timedelta(minutes=30 - start_time.minute % 30, 
                                         seconds=-start_time.second, 
                                         microseconds=-start_time.microsecond)
    return start_time
