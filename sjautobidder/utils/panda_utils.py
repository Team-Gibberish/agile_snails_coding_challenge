"""Utils that do frequently used conversions of pandas dataframes."""

import pandas as pd


def df_to_dict(df: pd.DataFrame) -> dict:
    """Converts pandas dicts to slightly better formatted dicts.

    The in-built pandas to_dict function does not convert indexes to strings
    which gives an error in MongoDB, as all keys need to be strings. This code
    converts all keys to strings.

    Args:
        df (pd.DataFrame) : The dataframe to convert to a dict

    Returns:
        converted_dict (dict) : A python dict with the data from the dataframe
    """
    dataframe_dict = df.to_dict()
    converted_dict = {
        outer_key: {
            str(inner_key): inner_value
            for inner_key, inner_value in outer_value.items()
        }
        for outer_key, outer_value in dataframe_dict.items()
    }

    return converted_dict
