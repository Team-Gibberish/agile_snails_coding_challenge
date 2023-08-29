"""This file contains functions that return the energy demand of the office site."""

import datetime
import numpy as np
import pandas as pd

from typing import List
from .energy_utils import get_temperatures, temp_to_energy, adjust_datetime
from .energy_utils import create_initial_demand_dataframe, get_active_office_mask

def get_energy_demand(
    start_time=None
) -> pd.DataFrame:
    """Get the energy demand for the building.

    Returns the total energy demand for the building over the next 24 hours,
    in 30 minute intervals.

    Args:
        start_time (datetime.datetime): The datetime to start predicting building demand from.

    Returns: pd.DataFrame: The total energy demand for the building over the next
        24 hours, in 30 minute intervals (48 instances).
    """
    if start_time is None:
        start_time = datetime.datetime.now().replace(hour=23, minute=0, second=0)
    start_time = adjust_datetime(start_time)

    demand_dataframe = create_initial_demand_dataframe(start_time)

    active_office_mask = get_active_office_mask(start_time)

    demand_dataframe["Heating"] = get_heating_demand(active_office_mask)
    demand_dataframe["Data Centre"] = get_data_centre_demand()
    demand_dataframe["Office Equipment"] = get_office_equipment_demand(
        active_office_mask
    )
    demand_dataframe["LightingOther"] = get_lighting_and_other_demand(
        active_office_mask
    )

    demand_dataframe["Total demand"] = demand_dataframe.sum(axis=1)

    return demand_dataframe


def get_heating_demand(active_office_mask: List[bool]) -> np.ndarray:
    """Get the energy demands for the building's heating system.

    Returns a numpy array of the energy demands of the heating system over
    the next 24 hours, in 30 minute intervals.

    Args:
        active_office_mask (List[bool]): An array of boolean values corresponding to whether
                                         people are in the office or not.

    Returns: np.ndarray: The energy demands of the heating system over the next
        24 hours, in 30 minute intervals (48 instances).
    """
    temperatures_over_coming_24_hours = get_temperatures()
    heating_demand = temp_to_energy(temperatures_over_coming_24_hours)
    heating_demand[~np.array(active_office_mask)] = 0

    return heating_demand

def get_data_centre_demand() -> np.ndarray:
    """Get the energy demand for the data center.
    Returns a numpy array with the energy demand of the data centre over the
    coming 24 hour period, in 30 minute intervals. Currently a dummy function.
    Returns: np.ndarray: The energy demands of the data center over the next 24
        hours, in 30 minute intervals (48 instances).
    """
    return np.ones(48) * 200

def get_office_equipment_demand(active_office_mask: List[bool]) -> np.ndarray:
    """Get the energy demand for the building's office equipment.

    Returns a numpy array with the energy demand of the office equipment over
    the coming 24 hour period, in 30 minute intervals.

    Args:
        active_office_mask (List[bool]): An array of boolean values corresponding to whether
                                         people are in the office or not.

    Returns: np.ndarray: The energy demands of the office equipment over the
        next 24 hours, in 30 minutes intervals (48 instances).
    """
    demand = np.array(active_office_mask) * 10
    return demand


def get_lighting_and_other_demand(active_office_mask: List[bool]) -> np.ndarray:
    """Get the energy demand for the building's lighting and miscellaneous equipment.

    Returns a numpy array with the energy demand of the lighting and 'other'
    energy demand over the coming 24 hour period, in 30 minute intervals.

    Args:
        active_office_mask (List[bool]): An array of boolean values corresponding to whether
                                         people are in the office or not.

    Returns: np.ndarray: The energy demands of the lighting and other equipment
        over the next 24 hours, in 30 minutes intervals (48 instances).
    """
    demand = np.array(active_office_mask) * 20
    return demand
