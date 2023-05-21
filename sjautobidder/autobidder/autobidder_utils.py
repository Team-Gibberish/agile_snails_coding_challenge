# -*- coding: utf-8 -*-
"""Functions to generate bid prices.
@author: jadot-bp
"""

import datetime as dt
import numpy as np
import pickle as p
import pandas as pd
import sklearn
from pathlib import Path

import sjautobidder.elexon_api.elexon_utils as elexon_utils


def _to_period(timestamp: dt.datetime) -> int:
    """Computes the market period from a given timestamp.

    Args:
        timestamp (dt.datetime) : Timestamp from which the associated market
                                  period is calculated.

    Returns:
        period (int) : Period corresponding to given timestamp.
    """

    assert isinstance(timestamp, (dt.datetime))

    minute_time = timestamp.hour * 60 + timestamp.minute

    period = minute_time // 30 + 1

    return period


def _to_time(period: int) -> str:
    """Computes timestamp from a given market period.

    Args:
        period (int) : Market period

    Returns:
        timestamp (str) : Timestamp in HH:MM corresponding to the market period
                          (to the nearest 30 minutes).
    """

    assert isinstance(period, int)

    hour = (period - 1) * 30 // 60
    minute = (period - 1) * 30 % 60

    return f"{hour:02}:{minute:02}"


def cache_forecast():
    """Caches the forecast for the following day."""

    # currently a placeholder function

    return None


def get_forecast(date: str, period: int) -> pd.DataFrame:
    """Fetches the elexon utilities and market data forecast for the specified
       time period.

    Args:
        date (str)   : Forecast date in format YYYY-MM-DD
        period (int) : Market period

    Returns:
        forecast (pd.DataFrame) : pd.DataFrame containing market forecast
                                  according to model pattern.
    """

    assert isinstance(date, str)
    assert isinstance(period, int)

    # Fetch generation per fuel type forecast
    gen_forecast = elexon_utils.get_bmrs_report("B1620", date, period)
    gen_forecast = elexon_utils.df_unstacker(
        gen_forecast,
        ["Settlement Date", "Settlement Period"],
        "Power System Resource  Type",
        "Quantity",
    )

    # Fetch forecast system load
    load_forecast = elexon_utils.get_bmrs_report("B0620", date, period)
    load_forecast = load_forecast[["Settlement Date", "Settlement Period", "Quantity"]]

    # Rename to conform to pattern
    load_forecast = load_forecast.rename(columns={"Quantity": "Load"})

    # Merge dataframes and clean
    output = pd.merge(
        gen_forecast, load_forecast, on=["Settlement Date", "Settlement Period"]
    )

    output.loc[:, "Settlement Date"] = pd.to_datetime(output["Settlement Date"])
    output.loc[:, "Settlement Date"] -= dt.datetime(1970, 1, 1)  # Since epoch
    output.loc[:, "Settlement Date"] = output.loc[:, "Settlement Date"].dt.days

    # Pattern dictates current feature arrangement for autobidder model

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

    """
    pattern = ["Settlement Date", "Settlement Period", "Load", "Solar",
               "Wind Offshore", "Wind Onshore"]
    """
    return output[pattern]


def get_price_estimate(date=None, period=None) -> (str, int, float):
    """Calculates the estimated market sell price for the given date and
       period.

    Args:
        date (str)   : Forecast date in format YYYY-MM-DD
        period (int) : Market period

    Returns:
        (str, int, float) tuple representing the forecast date, market period
        and predicted market price.
    """

    # Load autobidder ML model
    with open(Path(__file__).absolute().parent / "model.p", "rb") as handle:
        model = p.load(handle)

    # Load data scaler for autobidder
    with open(Path(__file__).absolute().parent / "scaler.p", "rb") as handle:
        scaler = p.load(handle)

    if date is None:
        date = dt.datetime.now()
        strdate = dt.datetime.strftime(date, "%Y-%m-%d")
    else:
        strdate = date
        date = dt.datetime.strptime(date, "%Y-%m-%d")

    if period is None:
        period = _to_period(dt.datetime.now())

    # Maximum time delta supported by ML model
    delta = (date - dt.datetime.now()).days * 48 + period

    if delta > 2 * 48:
        price = "NaN"
    else:
        lagged_date = date + dt.timedelta(days=-3)
        forecast = get_forecast(dt.datetime.strftime(lagged_date, "%Y-%m-%d"), period)
        rescaled = scaler.transform(forecast.values[:])

        price = model.predict(rescaled)[0]

    return strdate, period, price


def get_price_forecast() -> list:
    """Generates the Day-Ahead (11pm-11pm) market price forecast.

    Args:
        None

    Returns:
        np.ndarray : Array of market prices.
    """

    date = dt.datetime.strftime(dt.datetime.now(), "%Y-%m-%d")
    period = 47  # 11pm

    prices = []

    n_periods = 0

    while n_periods < 49:
        if period > 48:
            period = 1
            new_date = dt.datetime.now() + dt.timedelta(days=1)
            date = dt.datetime.strftime(new_date, "%Y-%m-%d")
        prices.append(get_price_estimate(date, period)[2])
        period += 1
        n_periods += 1

    return prices
