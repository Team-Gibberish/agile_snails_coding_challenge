"""Tests to ensure api utility functions are working correctly.

Todo:
    test_unpack_forecasts() Include testing for specific dictionary keys
    test_interpolate() Needs to include data value checking

    All tests lack edge cases, failing cases, and exception testing.
"""

import pickle
from typing import List, Tuple
import pandas as pd
import pytest
from requests.models import Response

from sjautobidder.met_office_api.api_utils import (
    count_forecasts,
    datetime_array,
    elevens,
    forecast_times_no24,
    interp_30min,
    unpack_forecasts,
)


@pytest.mark.parametrize(
    "response, hours, step, date_strings",
    [
        (
            pickle.load(open("tests/resources/14-May-2021-response.p", "rb")),
            60,
            3,
            [
                "2021-05-14T18:00:00Z",
                "2021-05-14T21:00:00Z",
                "2021-05-15T00:00:00Z",
                "2021-05-15T03:00:00Z",
                "2021-05-15T06:00:00Z",
                "2021-05-15T09:00:00Z",
                "2021-05-15T12:00:00Z",
                "2021-05-15T15:00:00Z",
                "2021-05-15T18:00:00Z",
                "2021-05-15T21:00:00Z",
                "2021-05-16T00:00:00Z",
                "2021-05-16T03:00:00Z",
                "2021-05-16T06:00:00Z",
                "2021-05-16T09:00:00Z",
                "2021-05-16T12:00:00Z",
                "2021-05-16T15:00:00Z",
                "2021-05-16T18:00:00Z",
                "2021-05-16T21:00:00Z",
                "2021-05-17T00:00:00Z",
                "2021-05-17T03:00:00Z",
                "2021-05-17T06:00:00Z",
            ],
        )  # Cached result for 14-May-2021
    ],
)
def test_datetime_array(
    response: Response, hours: int, step: int, date_strings: List[str]
):
    """Test datetime_array to ensure a correct list of datetime steps.

    Args:
        response (Response): Metoffice API response
        hours (int): The total number of hours covered by result array. Must be
            an exact multiple of step size.
        step (int): The step size between each hour.
        date_strings (List[str]): A list of expected datetime strings in the format
            of 2021-05-05T13:00:00Z
    """
    output = datetime_array(response, hours, step)
    print(output)

    # Assert Type
    assert isinstance(output, list)
    for value in output:
        assert isinstance(value, str)

    # Assert Values
    assert len(output) == len(date_strings)
    for i, value in enumerate(date_strings):
        assert value == output[i]


@pytest.mark.parametrize(
    "response, count",
    [
        (
            pickle.load(open("tests/resources/14-May-2021-response.p", "rb")),
            35,
        )  # Cached result for 14-May-2021
    ],
)
def test_count_forecasts(response: Response, count: int):
    """Test to ensure that forecasts are counted correctly.

    Args:
        response (Response): Metoffice API response
        count (int): Number of forecasts in the API response
    """
    output = count_forecasts(response)

    # Assert Type
    assert isinstance(output, int)

    # Assert Value
    assert output == count


@pytest.mark.parametrize(
    "response, cumulative_hours",
    [
        (
            pickle.load(open("tests/resources/14-May-2021-response.p", "rb")),
            [
                18,
                21,
                24,
                27,
                30,
                33,
                36,
                39,
                42,
                45,
                48,
                51,
                54,
                57,
                60,
                63,
                66,
                69,
                72,
                75,
                78,
                81,
                84,
                87,
                90,
                93,
                96,
                99,
                102,
                105,
                108,
                111,
                114,
                117,
                120,
                123,
            ],
        )
    ],
)
def test_forecast_times(response: Response, cumulative_hours: List[int]):
    """Ensure cumulative times over a response period are calculated correctly.

    Args:
        response (Response): Metoffice API response
        cumulative_hours (List[int]): List of cumulative hours
    """
    output = forecast_times_no24(response)

    # Assert Types
    assert isinstance(output, list)
    for value in output:
        assert isinstance(value, int)

    # Assert values
    assert len(output) == len(cumulative_hours)
    for i, value in enumerate(output):
        assert value == cumulative_hours[i]


@pytest.mark.parametrize(
    "response, unpacked",
    [
        (
            pickle.load(open("tests/resources/14-May-2021-response.p", "rb")),
            [
                {
                    "D": "S",
                    "F": "8",
                    "G": "11",
                    "H": "78",
                    "Pp": "55",
                    "S": "11",
                    "T": "10",
                    "V": "GO",
                    "W": "12",
                    "U": "2",
                    "$": "900",
                },
                {
                    "D": "S",
                    "F": "7",
                    "G": "13",
                    "H": "79",
                    "Pp": "16",
                    "S": "11",
                    "T": "10",
                    "V": "VG",
                    "W": "8",
                    "U": "1",
                    "$": "1080",
                },
                {
                    "D": "SW",
                    "F": "5",
                    "G": "9",
                    "H": "100",
                    "Pp": "94",
                    "S": "4",
                    "T": "7",
                    "V": "MO",
                    "W": "15",
                    "U": "0",
                    "$": "1260",
                },
                {
                    "D": "SSE",
                    "F": "5",
                    "G": "11",
                    "H": "92",
                    "Pp": "9",
                    "S": "4",
                    "T": "7",
                    "V": "GO",
                    "W": "7",
                    "U": "0",
                    "$": "0",
                },
                {
                    "D": "SE",
                    "F": "2",
                    "G": "16",
                    "H": "93",
                    "Pp": "88",
                    "S": "7",
                    "T": "5",
                    "V": "GO",
                    "W": "15",
                    "U": "0",
                    "$": "180",
                },
                {
                    "D": "SE",
                    "F": "3",
                    "G": "13",
                    "H": "97",
                    "Pp": "79",
                    "S": "7",
                    "T": "6",
                    "V": "PO",
                    "W": "15",
                    "U": "1",
                    "$": "360",
                },
                {
                    "D": "S",
                    "F": "7",
                    "G": "13",
                    "H": "90",
                    "Pp": "57",
                    "S": "7",
                    "T": "9",
                    "V": "MO",
                    "W": "14",
                    "U": "2",
                    "$": "540",
                },
                {
                    "D": "SW",
                    "F": "8",
                    "G": "18",
                    "H": "81",
                    "Pp": "56",
                    "S": "9",
                    "T": "10",
                    "V": "VG",
                    "W": "12",
                    "U": "4",
                    "$": "720",
                },
                {
                    "D": "W",
                    "F": "7",
                    "G": "18",
                    "H": "84",
                    "Pp": "52",
                    "S": "9",
                    "T": "10",
                    "V": "GO",
                    "W": "10",
                    "U": "2",
                    "$": "900",
                },
                {
                    "D": "WSW",
                    "F": "7",
                    "G": "16",
                    "H": "90",
                    "Pp": "69",
                    "S": "9",
                    "T": "9",
                    "V": "GO",
                    "W": "14",
                    "U": "1",
                    "$": "1080",
                },
                {
                    "D": "SW",
                    "F": "4",
                    "G": "16",
                    "H": "96",
                    "Pp": "52",
                    "S": "7",
                    "T": "7",
                    "V": "GO",
                    "W": "7",
                    "U": "0",
                    "$": "1260",
                },
                {
                    "D": "SW",
                    "F": "4",
                    "G": "16",
                    "H": "97",
                    "Pp": "16",
                    "S": "7",
                    "T": "7",
                    "V": "GO",
                    "W": "7",
                    "U": "0",
                    "$": "0",
                },
                {
                    "D": "SSW",
                    "F": "4",
                    "G": "13",
                    "H": "97",
                    "Pp": "57",
                    "S": "7",
                    "T": "6",
                    "V": "GO",
                    "W": "7",
                    "U": "0",
                    "$": "180",
                },
                {
                    "D": "SSW",
                    "F": "5",
                    "G": "11",
                    "H": "96",
                    "Pp": "45",
                    "S": "4",
                    "T": "7",
                    "V": "GO",
                    "W": "10",
                    "U": "1",
                    "$": "360",
                },
                {
                    "D": "SSW",
                    "F": "7",
                    "G": "13",
                    "H": "92",
                    "Pp": "64",
                    "S": "7",
                    "T": "9",
                    "V": "GO",
                    "W": "14",
                    "U": "3",
                    "$": "540",
                },
                {
                    "D": "SW",
                    "F": "9",
                    "G": "13",
                    "H": "84",
                    "Pp": "68",
                    "S": "7",
                    "T": "11",
                    "V": "GO",
                    "W": "14",
                    "U": "4",
                    "$": "720",
                },
                {
                    "D": "WSW",
                    "F": "9",
                    "G": "13",
                    "H": "83",
                    "Pp": "70",
                    "S": "7",
                    "T": "11",
                    "V": "MO",
                    "W": "14",
                    "U": "3",
                    "$": "900",
                },
                {
                    "D": "NW",
                    "F": "9",
                    "G": "11",
                    "H": "85",
                    "Pp": "61",
                    "S": "4",
                    "T": "10",
                    "V": "GO",
                    "W": "14",
                    "U": "1",
                    "$": "1080",
                },
                {
                    "D": "NW",
                    "F": "6",
                    "G": "9",
                    "H": "94",
                    "Pp": "36",
                    "S": "4",
                    "T": "7",
                    "V": "GO",
                    "W": "9",
                    "U": "0",
                    "$": "1260",
                },
                {
                    "D": "W",
                    "F": "5",
                    "G": "9",
                    "H": "96",
                    "Pp": "11",
                    "S": "4",
                    "T": "6",
                    "V": "MO",
                    "W": "7",
                    "U": "0",
                    "$": "0",
                },
                {
                    "D": "WNW",
                    "F": "4",
                    "G": "11",
                    "H": "97",
                    "Pp": "10",
                    "S": "4",
                    "T": "6",
                    "V": "MO",
                    "W": "7",
                    "U": "0",
                    "$": "180",
                },
                {
                    "D": "WNW",
                    "F": "5",
                    "G": "13",
                    "H": "95",
                    "Pp": "8",
                    "S": "7",
                    "T": "7",
                    "V": "MO",
                    "W": "7",
                    "U": "1",
                    "$": "360",
                },
                {
                    "D": "WNW",
                    "F": "7",
                    "G": "20",
                    "H": "80",
                    "Pp": "15",
                    "S": "9",
                    "T": "10",
                    "V": "GO",
                    "W": "7",
                    "U": "3",
                    "$": "540",
                },
                {
                    "D": "WNW",
                    "F": "8",
                    "G": "27",
                    "H": "73",
                    "Pp": "32",
                    "S": "11",
                    "T": "11",
                    "V": "GO",
                    "W": "10",
                    "U": "5",
                    "$": "720",
                },
                {
                    "D": "WNW",
                    "F": "7",
                    "G": "29",
                    "H": "67",
                    "Pp": "15",
                    "S": "13",
                    "T": "11",
                    "V": "GO",
                    "W": "7",
                    "U": "3",
                    "$": "900",
                },
                {
                    "D": "W",
                    "F": "6",
                    "G": "25",
                    "H": "73",
                    "Pp": "11",
                    "S": "11",
                    "T": "9",
                    "V": "GO",
                    "W": "7",
                    "U": "1",
                    "$": "1080",
                },
                {
                    "D": "W",
                    "F": "4",
                    "G": "16",
                    "H": "87",
                    "Pp": "11",
                    "S": "7",
                    "T": "7",
                    "V": "GO",
                    "W": "7",
                    "U": "0",
                    "$": "1260",
                },
                {
                    "D": "W",
                    "F": "4",
                    "G": "16",
                    "H": "89",
                    "Pp": "10",
                    "S": "7",
                    "T": "7",
                    "V": "GO",
                    "W": "7",
                    "U": "0",
                    "$": "0",
                },
                {
                    "D": "W",
                    "F": "2",
                    "G": "18",
                    "H": "92",
                    "Pp": "12",
                    "S": "7",
                    "T": "6",
                    "V": "GO",
                    "W": "7",
                    "U": "0",
                    "$": "180",
                },
                {
                    "D": "WSW",
                    "F": "3",
                    "G": "18",
                    "H": "90",
                    "Pp": "15",
                    "S": "7",
                    "T": "6",
                    "V": "GO",
                    "W": "7",
                    "U": "1",
                    "$": "360",
                },
                {
                    "D": "W",
                    "F": "6",
                    "G": "25",
                    "H": "77",
                    "Pp": "32",
                    "S": "11",
                    "T": "9",
                    "V": "GO",
                    "W": "10",
                    "U": "4",
                    "$": "540",
                },
                {
                    "D": "W",
                    "F": "8",
                    "G": "29",
                    "H": "66",
                    "Pp": "38",
                    "S": "13",
                    "T": "11",
                    "V": "GO",
                    "W": "10",
                    "U": "4",
                    "$": "720",
                },
                {
                    "D": "WSW",
                    "F": "8",
                    "G": "31",
                    "H": "67",
                    "Pp": "34",
                    "S": "13",
                    "T": "11",
                    "V": "GO",
                    "W": "10",
                    "U": "3",
                    "$": "900",
                },
                {
                    "D": "WSW",
                    "F": "7",
                    "G": "25",
                    "H": "75",
                    "Pp": "33",
                    "S": "11",
                    "T": "10",
                    "V": "GO",
                    "W": "10",
                    "U": "1",
                    "$": "1080",
                },
                {
                    "D": "WSW",
                    "F": "4",
                    "G": "18",
                    "H": "89",
                    "Pp": "15",
                    "S": "9",
                    "T": "7",
                    "V": "GO",
                    "W": "7",
                    "U": "0",
                    "$": "1260",
                },
            ],
        )
    ],
)
def test_unpack_forecasts(response: Response, unpacked: List[dict]):
    """Test to ensure response forecasts are unpacked correctly.

    Args:
        response (Response): Metoffice API response
        unpacked (List[dict]): A list of dictionaries representing the forecasts
            from the given API response.
    """
    output = unpack_forecasts(response)

    # Assert Types
    assert isinstance(output, list)
    for value in output:
        assert isinstance(value, dict)
        for key in value:
            # Assume all keys are strings
            assert isinstance(key, str)

    # Assert Values
    assert len(output) == len(unpacked)
    for i, forecast in enumerate(output):
        assert forecast == unpacked[i]


@pytest.mark.parametrize(
    "response, forcasts",
    [
        (
            pickle.load(open("tests/resources/14-May-2021-response.p", "rb")),
            (
                [
                    {
                        "D": "S",
                        "F": "7",
                        "G": "13",
                        "H": "79",
                        "Pp": "16",
                        "S": "11",
                        "T": "10",
                        "V": "VG",
                        "W": "8",
                        "U": "1",
                        "$": "1080",
                    },
                    {
                        "D": "SW",
                        "F": "5",
                        "G": "9",
                        "H": "100",
                        "Pp": "94",
                        "S": "4",
                        "T": "7",
                        "V": "MO",
                        "W": "15",
                        "U": "0",
                        "$": "1260",
                    },
                    {
                        "D": "SSE",
                        "F": "5",
                        "G": "11",
                        "H": "92",
                        "Pp": "9",
                        "S": "4",
                        "T": "7",
                        "V": "GO",
                        "W": "7",
                        "U": "0",
                        "$": "0",
                    },
                    {
                        "D": "SE",
                        "F": "2",
                        "G": "16",
                        "H": "93",
                        "Pp": "88",
                        "S": "7",
                        "T": "5",
                        "V": "GO",
                        "W": "15",
                        "U": "0",
                        "$": "180",
                    },
                    {
                        "D": "SE",
                        "F": "3",
                        "G": "13",
                        "H": "97",
                        "Pp": "79",
                        "S": "7",
                        "T": "6",
                        "V": "PO",
                        "W": "15",
                        "U": "1",
                        "$": "360",
                    },
                    {
                        "D": "S",
                        "F": "7",
                        "G": "13",
                        "H": "90",
                        "Pp": "57",
                        "S": "7",
                        "T": "9",
                        "V": "MO",
                        "W": "14",
                        "U": "2",
                        "$": "540",
                    },
                    {
                        "D": "SW",
                        "F": "8",
                        "G": "18",
                        "H": "81",
                        "Pp": "56",
                        "S": "9",
                        "T": "10",
                        "V": "VG",
                        "W": "12",
                        "U": "4",
                        "$": "720",
                    },
                    {
                        "D": "W",
                        "F": "7",
                        "G": "18",
                        "H": "84",
                        "Pp": "52",
                        "S": "9",
                        "T": "10",
                        "V": "GO",
                        "W": "10",
                        "U": "2",
                        "$": "900",
                    },
                    {
                        "D": "WSW",
                        "F": "7",
                        "G": "16",
                        "H": "90",
                        "Pp": "69",
                        "S": "9",
                        "T": "9",
                        "V": "GO",
                        "W": "14",
                        "U": "1",
                        "$": "1080",
                    },
                    {
                        "D": "SW",
                        "F": "4",
                        "G": "16",
                        "H": "96",
                        "Pp": "52",
                        "S": "7",
                        "T": "7",
                        "V": "GO",
                        "W": "7",
                        "U": "0",
                        "$": "1260",
                    },
                    {
                        "D": "SW",
                        "F": "4",
                        "G": "16",
                        "H": "97",
                        "Pp": "16",
                        "S": "7",
                        "T": "7",
                        "V": "GO",
                        "W": "7",
                        "U": "0",
                        "$": "0",
                    },
                ],
                [
                    "2021-05-14T21:00:00Z",
                    "2021-05-15T00:00:00Z",
                    "2021-05-15T03:00:00Z",
                    "2021-05-15T06:00:00Z",
                    "2021-05-15T09:00:00Z",
                    "2021-05-15T12:00:00Z",
                    "2021-05-15T15:00:00Z",
                    "2021-05-15T18:00:00Z",
                    "2021-05-15T21:00:00Z",
                    "2021-05-16T00:00:00Z",
                    "2021-05-16T03:00:00Z",
                ],
            ),
        )
    ],
)
def test_elevens(response: Response, forcasts: Tuple[List[dict], List[str]]):
    """Ensure forecasts are datetimed stamped correctly.

    Args:
        response (Response): Metoffice API response
        forcasts (Tuple[List[dict], List[str]]): A list of forecasts along with
            their datetime stamp
    """
    output = elevens(response)
    print(output)

    # Assert Types
    assert isinstance(output, tuple)

    assert isinstance(output[0], list)
    assert isinstance(output[1], list)

    for value in output[0]:
        assert isinstance(value, dict)

    for value in output[1]:
        assert isinstance(value, str)

    # Assert Values
    assert output == forcasts


@pytest.mark.parametrize(
    "response, data",
    [
        (
            pickle.load(open("tests/resources/14-May-2021-response.p", "rb")),
            pd.read_csv(
                "tests/resources/14-May-2021-interpolated.csv",
                sep=",",
                header=0,
                index_col=0,
            ),
        )
    ],
)
def test_interpolate(response: Response, data: pd.DataFrame):
    """Test to see if interpolated results are generated correctly.

    Args:
        response (Response): Metoffice API response
        data (pd.DataFrame): A dataframe of an interpolated forcast corresponding
            to the given Metoffice API response.
    """
    output = interp_30min(response)

    # Assert Type
    assert isinstance(output, pd.DataFrame)

    # assert number of records
    assert output.shape[0] == 60

    # assert columns
    assert output.shape[1] == 12

    # Assert Column Types
    assert output.dtypes.to_dict() == {
        "D": object,  # str
        "F": float,
        "G": float,
        "H": float,
        "Pp": float,
        "S": float,
        "T": float,
        "V": object,  # str
        "W": int,
        "U": int,
        "$": float,
        "DateTime": object,  # str
    }

    # Assert Values
    for row in output:
        for i, value in enumerate(output[row]):
            assert value == pytest.approx(data[row][i])
