"""Tests to ensure bidder_utils.py is working as expected.
"""

import pytest
import datetime as dt
import pandas as pd
import numpy as np

from sjautobidder.autobidder.autobidder_utils import (
    get_forecast,
    get_price_estimate,
    get_price_forecast,
)

@pytest.mark.parametrize(
    "date, period",
    [("2020-01-01", 1), ("2020-01-01", 10), ("2020-01-01", 29)],)
def test_get_forcast(date, period):
    """Tests to ensure get_forcast is working as expected.
    """
    pattern = [
        "Settlement Date",
        "Settlement Period",
        "Biomass",
        "Hydro Pumped Storage",
        "Hydro Run-of-river and poundage",
        "Fossil Hard coal",
        "Fossil Gas",
        "Fossil Oil",
        "Nuclear",
        "Other",
        "Load",
        "Solar",
        "Wind Offshore",
        "Wind Onshore",
    ]

    output = get_forecast(date, period)
    assert isinstance(output, pd.DataFrame)
    assert output.columns.tolist() == pattern

@pytest.mark.parametrize(
    "date, period",
    [("2020-01-01", 1), ("2020-01-01", 10), ("2020-01-01", 29)],)
def test_get_price_estimate(date, period):
    """Tests to ensure get_price_estimate is working as expected.
    """

    output = get_price_estimate(date, period)
    assert isinstance(output, tuple)


def test_get_price_forecast():

    output = get_price_forecast()
    assert isinstance(output, np.ndarray)
    assert output.shape == (48,)

