# -*- coding: utf-8 -*-
"""Functions to obtain forecast data from the Met Office API.

Created on Wed Mar 17 15:10:20 2021

@author: Matt
"""

import os
import os.path as path

import requests
from requests import Response
from sjautobidder.cache import cache_get_hashed, cache_save_hashed
from sjautobidder.met_office_api.api_utils import interpolate_api_response

METOFFICE_KEY_PATH = "../../metoffice-api-key.txt"


def get_metoffice_key() -> str:
    """Obtain the key used for met office API requests.

    Raises:
        RuntimeError: Raised if the key is not available in a local file, and not
            in the environment variables.

    Returns:
        str: Met office API key
    """
    current_directory = path.dirname(__file__)
    api_key_path = path.normpath(path.join(current_directory, METOFFICE_KEY_PATH))

    if os.path.exists(api_key_path):
        # attempt to read key from file
        try:
            with open(api_key_path, "r") as file:
                return file.read().strip()
        except OSError:
            # Ignore error
            pass

    # Try to get key from environment variable
    if "METOFFICEAPI" in os.environ:
        return os.environ["METOFFICEAPI"]

    # unable to obtain key, throw an error
    raise RuntimeError


def fetch_forecast():
    api_key = get_metoffice_key()

    base_metoffice_url = "http://datapoint.metoffice.gov.uk/public/data/"
    resource = "val/wxfcs/all/json/3507"
    url = base_metoffice_url + resource

    # Attempt to get from cache
    # response = cache_get_hashed(f"{url}, params=res: 3hourly, key: {api_key}")
    response = None
    if response is None or not isinstance(response, Response):
        # No result cached, use API
        response = requests.get(url, params={"res": "3hourly", "key": api_key})
        # cache_save_hashed(f"{url}, params=res: 3hourly, key: {api_key}", response)

    assert response.status_code == 200  # check response is good
    return response


def get_forecast():
    """Queries the met office API, interpolates the response to 1 hour intervals,
    and returns the results for the next 11pm-11pm interval.

    Returns: pd.DataFrame: Hourly forcasts for the next 23:00 - 23:00 interval
    """
    return interpolate_api_response(fetch_forecast())
