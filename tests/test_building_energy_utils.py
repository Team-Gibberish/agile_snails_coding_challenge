"""Tests to ensure office energy utility functions are working correctly.

Todo:
    test_get_active_office_mask() Needs updating with some actual test cases
    test_get_next_24_hour_datetime() Needs updating with some sensible test cases
"""
import datetime
from typing import List

import pytest
from sjautobidder.building_demand.energy_utils import (
    get_active_office_mask,
    get_next_24_hour_datetime,
    temp_to_energy,
)


@pytest.mark.parametrize(
    "temp, expect",
    [(-20, 120), (-5, 120), (0, 90), (5, 60), (10, 30), (15, 0), (20, 0)],
)
def test_temp_to_energy(temp, expect):
    """Test to ensure heating energy demand is calculated correctly.

    Args:
        temp (int): Outside Tempreture
        expect (int): Expected energy result
    """
    output = temp_to_energy(temp)

    # Assert type
    assert isinstance(output, int)

    # Assert Value
    assert output == expect


@pytest.mark.parametrize(
    "date, working_hours",
    [
        (datetime.datetime(2021, 5, 10), 17),  # Monday
        (datetime.datetime(2021, 5, 11), 17),  # Tuesday
        (datetime.datetime(2021, 5, 12), 17),  # Wednesday
        (datetime.datetime(2021, 5, 13), 17),  # Thursday
        (datetime.datetime(2021, 5, 14), 17),  # Friday
        (datetime.datetime(2021, 5, 15), 0),  # Saturday
        (datetime.datetime(2021, 5, 16), 0),  # Sunday
    ],
)
def test_get_active_office_mask(date: datetime.datetime, working_hours: int):
    """Ensure office occupancy mask is generated correctly.

    Args:
        date (datetime.datetime): Date to generate the office occupancy mask
        working_hours (int): Total working hours throughout the given day
    """
    output = get_active_office_mask(date)

    # Assert Types
    assert isinstance(output, list)

    for value in output:
        assert isinstance(value, bool)

    # Assert Values
    true_count = 0
    false_count = 0

    for val in output:
        if val:
            true_count += 1
        else:
            false_count += 1

    assert true_count == working_hours
    assert false_count == (48 - working_hours)
    assert len(output) == 48


@pytest.mark.parametrize(
    "date, times",
    [
        (
            datetime.datetime(2020, 5, 12),
            [
                datetime.datetime(2020, 5, 12, 0, 0),
                datetime.datetime(2020, 5, 12, 0, 30),
                datetime.datetime(2020, 5, 12, 1, 0),
                datetime.datetime(2020, 5, 12, 1, 30),
                datetime.datetime(2020, 5, 12, 2, 0),
                datetime.datetime(2020, 5, 12, 2, 30),
                datetime.datetime(2020, 5, 12, 3, 0),
                datetime.datetime(2020, 5, 12, 3, 30),
                datetime.datetime(2020, 5, 12, 4, 0),
                datetime.datetime(2020, 5, 12, 4, 30),
                datetime.datetime(2020, 5, 12, 5, 0),
                datetime.datetime(2020, 5, 12, 5, 30),
                datetime.datetime(2020, 5, 12, 6, 0),
                datetime.datetime(2020, 5, 12, 6, 30),
                datetime.datetime(2020, 5, 12, 7, 0),
                datetime.datetime(2020, 5, 12, 7, 30),
                datetime.datetime(2020, 5, 12, 8, 0),
                datetime.datetime(2020, 5, 12, 8, 30),
                datetime.datetime(2020, 5, 12, 9, 0),
                datetime.datetime(2020, 5, 12, 9, 30),
                datetime.datetime(2020, 5, 12, 10, 0),
                datetime.datetime(2020, 5, 12, 10, 30),
                datetime.datetime(2020, 5, 12, 11, 0),
                datetime.datetime(2020, 5, 12, 11, 30),
                datetime.datetime(2020, 5, 12, 12, 0),
                datetime.datetime(2020, 5, 12, 12, 30),
                datetime.datetime(2020, 5, 12, 13, 0),
                datetime.datetime(2020, 5, 12, 13, 30),
                datetime.datetime(2020, 5, 12, 14, 0),
                datetime.datetime(2020, 5, 12, 14, 30),
                datetime.datetime(2020, 5, 12, 15, 0),
                datetime.datetime(2020, 5, 12, 15, 30),
                datetime.datetime(2020, 5, 12, 16, 0),
                datetime.datetime(2020, 5, 12, 16, 30),
                datetime.datetime(2020, 5, 12, 17, 0),
                datetime.datetime(2020, 5, 12, 17, 30),
                datetime.datetime(2020, 5, 12, 18, 0),
                datetime.datetime(2020, 5, 12, 18, 30),
                datetime.datetime(2020, 5, 12, 19, 0),
                datetime.datetime(2020, 5, 12, 19, 30),
                datetime.datetime(2020, 5, 12, 20, 0),
                datetime.datetime(2020, 5, 12, 20, 30),
                datetime.datetime(2020, 5, 12, 21, 0),
                datetime.datetime(2020, 5, 12, 21, 30),
                datetime.datetime(2020, 5, 12, 22, 0),
                datetime.datetime(2020, 5, 12, 22, 30),
                datetime.datetime(2020, 5, 12, 23, 0),
                datetime.datetime(2020, 5, 12, 23, 30),
            ],
        )
    ],
)
def test_get_next_24_hour_datetime(
    date: datetime.datetime, times: List[datetime.datetime]
):
    """Check if datetime function returns correct datetimes.

    Args:
        date (datetime.datetime): Date to obtain the time slices of.
        times (List[datetime.datetime]): A list of datetimes of 30 minute intervals
            throughout the given date.
    """
    output = get_next_24_hour_datetime(date)

    # Assert Types
    assert isinstance(output, list)
    for value in output:
        assert isinstance(value, datetime.datetime)

    # Assert Values
    assert len(output) == 48

    for i, value in enumerate(output):
        assert value == times[i]
