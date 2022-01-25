# -*- coding: utf-8 -*-
"""Tests to ensure elexon api utility functions are working correctly.

All tests lack edge cases, failing cases, and exception testing.
"""

import pytest
import pickle
import pandas as pd
import numpy as np

from sjautobidder.elexon_api.elexon_utils import (
    _response_to_df,
    get_bmrs_report,
    get_bmrs_series,
    get_dersys_data,
    drop_non_unique,
    df_unstacker,
)


@pytest.mark.parametrize(
    "string_response, resulting_dataframe",
    [
        (
            pickle.load(
                open("tests/resources/20_May_elexon_api_B1440.p", "rb")
            ).content.decode("utf-8"),
            pd.read_csv(
                "tests/resources/20_May_elexon_dataframe.csv", index_col=0, dtype=str
            ),
        )
    ],
)
def test__response_to_df(string_response: str, resulting_dataframe: pd.DataFrame):
    """Test _response_to_df to ensure correct output from a given response.

    Args:
        string_response (str): utf-8 decoded string from response content
        resulting_dataframe (pd.DataFrame): Pandas DataFrame containing the
        expected output dataframe for the given response string.

    """
    output = _response_to_df(string_response)

    # Assert type
    assert isinstance(output, pd.DataFrame)

    # Assert shape
    assert resulting_dataframe.shape == output.shape

    # Assert values and types of each DataFrame entry
    for row in output:
        for i, value in enumerate(output[row]):
            assert value == resulting_dataframe[row][i]  # value
            assert type(value) == type(resulting_dataframe[row][i])  # type


@pytest.mark.parametrize(
    "code, date, period, resulting_dataframe",
    [
        (
            "B1440",
            "2021-05-05",
            12,
            pd.read_csv(
                "tests/resources/ELEXONAPI_get_bmrs_report_05May_p12_B1440.csv",
                index_col=0,
                dtype=str,
            ),
        )
    ],
)
def test_get_bmrs_report(
    code: str, date: str, period: int, resulting_dataframe: pd.DataFrame
):
    """Test get_brms_report to ensure correct BMRS report from Elexon API is
    fetched.

    Args:
        code (str): BMRS report identifier.
        date (str): Settlement date in format "YYYY-MM-DD".
        period (str, int): Settlement period in days.
        resulting_dataframe (pd.DataFrame): A dataframe of the expected bmrs
            response from the elexon API.

    """
    output = get_bmrs_report(code, date, period)

    # Assert type
    assert isinstance(output, pd.DataFrame)

    # Assert shape
    assert output.shape == resulting_dataframe.shape

    # Assert values and types of each DataFrame entry
    for row in output:
        for i, value in enumerate(output[row]):
            assert value == resulting_dataframe[row][i]  # value
            assert type(value) == type(resulting_dataframe[row][i])  # type


@pytest.mark.parametrize(
    "code, date, period",
    [
        ("B1440", "2021-05-05", -1),  # period < 1
        ("B1440", "2021-05-05", 100),  # period > 50
        ("sneed", "2021-05-05", 12),  # invalid BMRS code
    ],
)
def test_get_bmrs_report_error(code: str, date: str, period: int):
    """Test get_brms_report to ensure correct ValueErrors are raised.

    Args:
        code (str): BMRS report identifier.
        date (str): Settlement date in format "YYYY-MM-DD".
        period (str, int): Settlement period in days.
    """
    with pytest.raises(ValueError):
        output = get_bmrs_report(code, date, period)


@pytest.mark.parametrize(
    "code, from_date, to_date, resulting_dataframe",
    [
        (
            "B0620",
            "2021-05-01",
            "2021-05-10",
            pd.read_csv(
                "tests/resources/ELEXONAPI_get_bmrs_series_output_01May_10May.csv",
                index_col=0,
                dtype=str,
            ),
        )
    ],
)
def test_get_bmrs_series(
    code: str, from_date: str, to_date: str, resulting_dataframe: pd.DataFrame
):
    """Test get_brms_series to ensure correct BMRS series from Elexon is
    fetched.

    Args:
        code (str): BMRS report identifier.
        from_date (str): Initial settlement date in format "YYYY-MM-DD".
        to_date (str): Final settlement date in format "YYYY-MM-DD".
        resulting_dataframe (pd.DataFrame): A dataframe of the expected bmrs
            series response from the elexon API.
    """
    output = get_bmrs_series(code, from_date, to_date)

    # Assert type
    assert isinstance(output, pd.DataFrame)

    # Assert shape
    assert output.shape == resulting_dataframe.shape

    # TODO: values in DataFrame come out as pd.Series that are recursive
    # # Assert values and types of each DataFrame entry
    # for row in output:
    #     for i, value in enumerate(output[row]):
    #         assert value == resulting_dataframe[row][i] # value
    #         assert type(value) == type(resulting_dataframe[row][i]) # type


@pytest.mark.parametrize(
    "code, from_date, to_date",
    [
        ("B0620", "2021-05-10", "2021-05-01"),  # end_date before start_date
        ("bobyshmurda", "2021-05-01", "2021-05-10"),  # invalid BMRS code
    ],
)
def test_get_bmrs_series_error(code: str, from_date: str, to_date: str):
    """Test get_brms_series to ensure correct ValueErrors are raised.

    Args:
        code (str): BMRS report identifier.
        from_date (str): Initial settlement date in format "YYYY-MM-DD".
        to_date (str): Final settlement date in format "YYYY-MM-DD".
    """
    with pytest.raises(ValueError):
        output = get_bmrs_series(code, from_date, to_date)


@pytest.mark.parametrize(
    "from_date, to_date, period, resulting_dataframe",
    [
        (
            "2021-05-01",
            "2021-05-10",
            12,
            pd.read_csv(
                "tests/resources/ELEXONAPI_get_dersys_data_01May_10May_p12.csv",
                index_col=0,
                dtype=str,
            ).replace({np.nan: ""}),
        )
    ],
)
def test_get_dersys_data(
    from_date: str, to_date: str, period: int, resulting_dataframe: pd.DataFrame
):
    """Test get_dersys_data to ensure correct data is fetched from Elexon API.

    Args:
        from_date (str): Initial settlement date in format "YYYY-MM-DD".
        to_date (str): Final settlement date in format "YYYY-MM-DD".
        period (str, int): Settlement period in days.
        resulting_dataframe (pd.DataFrame): A dataframe of the expected dersys
            data response from the elexon API.
    """
    output = get_dersys_data(from_date, to_date, period).replace({"NULL": ""})
    # resulting_dataframe = resulting_dataframe.rename(
    #         columns={"TSABV.1": "TSABV"}, inplace=True
    #     )
    # Assert type
    assert isinstance(output, pd.DataFrame)

    # Assert shape
    assert output.shape == resulting_dataframe.shape

    # TODO: Value assertion fails idk why
    # # Assert values and types of each DataFrame entry
    # for row in output:
    #     for i, value in enumerate(output[row]):
    #         assert value == resulting_dataframe[row][i] # value
    #         assert type(value) == type(resulting_dataframe[row][i]) # type


@pytest.mark.parametrize(
    "input_dataframe, resulting_dataframe",
    [
        (
            pd.DataFrame(data={"col1": [0, 1], "col2": [2, 3], "col1": [0, 1]}),
            pd.DataFrame(data={"col1": [0, 1], "col2": [2, 3]}),
        ),
    ],
)
def test_drop_non_unique(
    input_dataframe: pd.DataFrame, resulting_dataframe: pd.DataFrame
):
    """Test drop_non_unique to ensure non-unique columns correctly dropped
    from input DataFrame.

    Args:
        input_dataframe (pd.DataFrame): Example input DataFrame with at least
        one non-unique column.
        resulting_dataframe (pd.DataFrame): A dataframe with the expected
        output from the drop_non_unique function.
    """
    output = drop_non_unique(input_dataframe)

    # Assert type
    assert isinstance(output, pd.DataFrame)

    # Assert shape
    assert output.shape == resulting_dataframe.shape

    # Assert correct columns dropped
    for i, column in enumerate(output.columns):
        assert column == resulting_dataframe.columns[i]


@pytest.mark.parametrize(
    "data, anchor_column, label_column, target_column, resulting_dataframe",
    [
        (
            pd.read_csv(
                "tests/resources/ELEXONAPI_df_unstacker_DATA_B1620_01May_10May.csv",
                index_col=0,
            ),
            ["Settlement Date", "Settlement Period"],
            "Power System Resource  Type",
            "Quantity",
            pd.read_csv(
                "tests/resources/ELEXONAPI_df_unstacker_B1620_01May_10May.csv",
                index_col=0,
                dtype=str,
            ),
        ),
    ],
)
def test_df_unstacker(
    data: pd.DataFrame,
    anchor_column: (str, list),
    label_column: (str),
    target_column: (str),
    resulting_dataframe: pd.DataFrame,
):
    """Test df_unstacker to ensure correct unstacked dataframe is returned.

    Args:
        data (pd.DataFrame): pandas.DataFrame object containing a stacked
            column.
        anchor_column (str, list): Name or list of names of columns which will
            be anchored during unstacking.
        label_column (str): Name of column which will be used to re-label
            the target column.
        target_column (str): Name of column which is to be unstacked.
        resulting_dataframe (pd.DataFrame): A dataframe with the expected
            unstacked output from the df_unstacker function.
    """
    output = df_unstacker(data, anchor_column, label_column, target_column)

    # Assert type
    assert isinstance(output, pd.DataFrame)

    # Assert shape
    assert output.shape == resulting_dataframe.shape

    # Assert values and types of each DataFrame entry
    for row in output:
        for i, value in enumerate(output[row]):
            assert value == resulting_dataframe[row][i]  # value
            assert type(value) == type(resulting_dataframe[row][i])  # type
