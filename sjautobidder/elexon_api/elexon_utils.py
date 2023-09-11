# -*- coding: utf-8 -*-
"""Functions to collect energy market data from Elexon.

@author: jadot-bp
"""

import datetime as dt
from typing import List, Optional, Union

import os
import os.path as path
import numpy as np
import pandas as pd
import requests
from requests import Response
from sjautobidder.cache import cache_get_hashed, cache_save_hashed

ELEXON_KEY_PATH = "../../elexon-api-key.txt"

CODE_DESCRIPTORS = {
    "B1720": "Amount of balancing reserves under contract",
    "B1730": "Prices of procured balancing reserves",
    "B1740": "Accepted aggregated offers",
    "B1750": "Activated balancing energy",
    "B1760": "Prices of activated balancing energy",
    "B1770": "Imbalance prices",
    "B1780": "Aggregated imbalance volumes",
    "B1810": ("CrossBorder balancing volumes of exchanged bids" " and offers"),
    "B1820": "CrossBorder balancing prices",
    "B1830": "CrossBorder balancing energy activated",
    "B0610": "Actual total load per bidding zone",
    "B0620": "Day ahead total load forecast per bidding zone",
    "B1430": "Day ahead aggregated generation",
    "B1440": "Generation forecasts for wind and solar",
    "B1610": "Actual generation output per generation unit",
    "B1620": "Actual aggregated generation perType",
    "B1630": ("Actual or estimated wind and solar power" " generation"),
    "B1320": "Congestion management measure counter-trading",
}


def get_elexon_key() -> str:
    """Obtain the key used for Elexon API requests.
    Raises:
        RuntimeError: Raised if the key is not available in a local file, and not
            in the environment variables.
    Returns:
        str: Elexon API key
    """
    current_directory = path.dirname(__file__)
    api_key_path = path.normpath(path.join(current_directory, ELEXON_KEY_PATH))

    if os.path.exists(api_key_path):
        # attempt to read key from file
        try:
            with open(api_key_path, "r") as file:
                return file.read().strip()
        except OSError:
            # Ignore error
            pass

    # Try to get key from environment variable
    if "ELEXONAPI" in os.environ:
        return os.environ["ELEXONAPI"]

    # unable to obtain key, throw an error
    raise RuntimeError


def _response_to_df(response_string: str, code: str) -> pd.DataFrame:
    """Converts utf-8 decoded response string to a pandas.DataFrame object.

    Args:
        response_string (str) : utf-8 decoded string from response content
        code (str)          : BMRS report identifier (e.g. "B1440")

    Returns:
        pandas.DataFrame object
    """
    assert len(response_string) != 0

    # Unpack csv formatted response_string
    data_string = response_string.split("\n")
    header = data_string[4].split(",")
    header[0] = header[0].lstrip("*")  # Catch leading asterisk
    content = [x.split(",") for x in data_string[5:-1]]

    if code == "B1620":
        return pd.DataFrame(content, columns=header).iloc[-11:] # If there are old values included in the bmrs, only choose newer value.
    else:
        return pd.DataFrame(content, columns=header)


def get_bmrs_report(code: str, date: str, period="*") -> pd.DataFrame:
    """Fetches the specified BMRS report from Elexon.

    Fetches the specified BMRS report from Elexon. and returns a
    pandas.DataFrame object containing the report results.

    Args:
        code (str)          : BMRS report identifier (e.g. "B1440")
        date (str)          : Settlement date
        period (str, int)   : Settlement period (optional, default is `*`)

    Returns:
        pandas.DataFrame object

    Raises:
        ValueError  : if period not between 1-50 inclusive
        ValueError  : if code not in the list of supported BMRS codes
    """

    APIKEY = get_elexon_key()

    if period == "*":
        pass
    elif int(period) < 1 or int(period) > 50:
        raise ValueError(
            "period must be a str or int representing a number"
            " between 1-48 (inclusive) for a 24 hour day. Default"
            " period is `*` for all periods."
        )

    if code not in CODE_DESCRIPTORS.keys():
        raise ValueError(
            f"code {code} either an invalid BMRS code or is not" " yet supported"
        )

    assert isinstance(code, str)
    assert isinstance(date, str)

    url = (
        f"https://api.bmreports.com/BMRS/{code}/v1?APIKey={APIKEY}"
        f"&SettlementDate={date}&Period={period}&ServiceType=csv"
    )

    # Attempt response from cache
    response = cache_get_hashed(url)
    if response is None or not isinstance(response, Response):
        # No result cached, use API
        response = requests.get(url)
        cache_save_hashed(url, response)

    assert response.status_code == 200

    return _response_to_df(response.content.decode("utf-8"), code)


def get_bmrs_series(code: str, from_date_str: str, to_date_str: str) -> pd.DataFrame:
    """Collates a series of Day-Ahead BMRS reports into a single dataframe.

    Collates a series of Day-Ahead BMRS reports into a single pandas.DataFrame
    containing the BMRS reporting between the specified dates (inclusive).

    Args:
        code (str)          : BMRS report identifier (e.g. "B1440")
        from_date_str (str)     : Initial settlement date ("YYYY-MM-DD")
        to_date_str (str)       : Final settlement date ("YYYY-MM-DD")

    Returns:
        pandas.DataFrame object

    Raises:
        ValueError  : if end_date is before start_date
        ValueError  : if code not in the list of supported BMRS codes
    """
    assert isinstance(code, str)
    assert isinstance(from_date_str, str)
    assert isinstance(to_date_str, str)

    # Recast dates as datetime.datetime objects
    from_date = dt.datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = dt.datetime.strptime(to_date_str, "%Y-%m-%d")

    if from_date > to_date:
        raise ValueError("from_date must be before to_date.")

    if code not in CODE_DESCRIPTORS.keys():
        raise ValueError(
            f"code {code} either an invalid BMRS code or is not" " yet supported"
        )

    series = pd.DataFrame()  # Initialise empty data frame for series

    loop_date = from_date  # loop_date counter to iterate over dates

    while loop_date <= to_date:
        date_string = dt.datetime.strftime(loop_date, "%Y-%m-%d")
        try:
            data = get_bmrs_report(code, date_string, period="*")
        except IndexError:  # Catch responses with no data
            data = pd.DataFrame([date_string], columns=["Settlement Date"])
        series = pd.concat([series, data])
        loop_date += dt.timedelta(days=1)

    return series


def get_dersys_data(from_date: str, to_date: str, period=None) -> pd.DataFrame:
    """Fetch derived system wide data.

    Fetches derived system wide data for the dates specified and returns a
    pandas.DataFrame object containing the system report.

    Args:
        from_date (str)     : Initial settlement date ("YYYY-MM-DD")
        to_date (str)       : Final settlement date ("YYYY-MM-DD")
        period (str, int)   : Settlement period (optional, default is None)

    Returns:
        pandas.DataFrame object
    """

    APIKEY = get_elexon_key()

    assert isinstance(from_date, str)
    assert isinstance(to_date, str)
    assert type(period) in [str, int, type(None)]

    pstring = ""

    if period is not None:
        pstring = f"&Period={period}"  # Catch optional period parameter

    url = (
        f"https://api.bmreports.com/BMRS/DERSYSDATA/v1?APIKey={APIKEY}"
        f"&FromSettlementDate={from_date}&ToSettlementDate={to_date}"
        f"{pstring}&ServiceType=csv"
    )

    header = [
        "Record",
        "Settlement Date",
        "Settlement Period",
        "SSP (£/MWh)",
        "SBP (£/MWh)",
        "BSAD",
        "PDC",
        "RSP",
        "NIV",
        "RP (£/MWh)",
        "RPRV (MWh)",
        "TSAOV",
        "TSABV",
        "TSTAOV",
        "TSTABV",
        "STPAOV",
        "STPABV",
        "TSASV",
        "TSABV",
        "TSTAdSV",
        "TSTAdBV",
    ]

    # Attempt response from cache
    response = cache_get_hashed(url)
    if response is None or not isinstance(response, Response):
        # No result cached, use API
        response = requests.get(url)
        cache_save_hashed(url, response)

    assert response.status_code == 200

    raw_string = response.content.decode("utf-8")
    data_string = raw_string.split("\n")
    content = [x.split(",") for x in data_string[1:-1]]

    return pd.DataFrame(content, columns=header)


def drop_non_unique(
    dataframe: pd.DataFrame, keep_cols: Optional[Union[str, List[str]]] = None
) -> pd.DataFrame:
    """Drop non-unique columns.

    Drops columns with non-unique entries and returns a new pandas.DataFrame
    object.

    Args:
        dataframe (pd.DataFrame) : pandas.DataFrame object
        keep_cols (str,list)     : string or list of strings corresponding to
                                   the column headers that are to be kept.

    Returns:
        pandas.DataFrame object
    """
    assert isinstance(dataframe, pd.DataFrame)

    new_dataframe = dataframe.copy()
    for cname in new_dataframe.columns.values:
        if keep_cols is None or cname in keep_cols:
            pass
        elif len(new_dataframe[cname].unique()) == 1:
            new_dataframe = new_dataframe.drop(columns=cname)

    return new_dataframe


def df_unstacker(
    data: pd.DataFrame,
    anchor_column: Union[str, list],
    label_column: str,
    target_column: str,
) -> pd.DataFrame:
    """Unstack a stacked dataframe.

    Unstacks a target column of a pandas.DataFrame object with respect to a
    specified anchor column(s), returning a new pandas.DataFrame with the
    target column relabelled according to the label column.

    Args:
        data (pd.DataFrame)              : pandas.DataFrame object containing a
                                           stacked column
        anchor_column (Union[str, list]) : Name or list of names of columns which
                                           will be anchored during unstacking
        label_column (str)               : Name of column which will be used to
                                           re-label the target column
        target_column (str)              : Name of column which is to be unstacked
    Returns:
        pd.DataFrame: unstacked data
    """
    assert isinstance(data, pd.DataFrame)
    assert isinstance(anchor_column, (str, list))
    assert isinstance(label_column, str)
    assert isinstance(target_column, str)

    # Generate temporary dataframe to collect unique anchor values
    temp_df = data[anchor_column].drop_duplicates()

    unique_values = []
    for anchor_label in anchor_column:
        unique_values.append(temp_df[anchor_label].values[:])

    out_df = pd.DataFrame()  # Prepare empty dataframe for concatenation

    # Iterate through possible unique pairs of anchor values
    for pos, unique_pair in enumerate(list(zip(*unique_values))):

        mask = 0  # Create mask to slice out anchored values
        for label_pos, anchor_label in enumerate(anchor_column):
            mask += (data[anchor_label] == unique_pair[label_pos]).values[:]
        mask = mask // len(anchor_column)  # Integer division gets boolean mask

        temp_df = drop_non_unique(data[mask.astype(bool)], target_column)
        temp_df = temp_df[[label_column, target_column]]

        headers = [i.strip('"') for i in temp_df[label_column].unique()]
        quantities = list(temp_df[target_column])

        # Add anchor names and values to headers and quantities
        headers = list(anchor_column) + headers
        quantities = list(unique_pair) + quantities

        # Construct new unstacked dataframe
        unstacked_df = pd.DataFrame(
            np.asarray(quantities).reshape(1, -1), columns=headers, index=[pos]
        )

        # Concatenate with output dataframe
        out_df = pd.concat((out_df, unstacked_df), axis=0, ignore_index=True)

    return out_df
