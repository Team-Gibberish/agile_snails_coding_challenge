import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

import sjautobidder.elexon_api.elexon_utils
from sjautobidder.power_integration.power_estimation import main as estimate_power

# ######################### Things related to mocking #########################
# This following part mocks out API calls for now, so that you can test the code
# without the need to set up API keys and have an internet connection. You can
# safely ignore this part for now.

DATA_DIRECTORY = Path(__file__).absolute().parent / "dummy_data"

MARKET_DATAFILE = DATA_DIRECTORY / "market_index.csv"
LOAD_TEMPLATE = DATA_DIRECTORY / "load_template.csv"
GENERATION_TEMPLATE = DATA_DIRECTORY / "generation_template.csv"
METOFFICE_TEMPLATE = DATA_DIRECTORY / "met_office_template.json"
METOFFICE_DATAFILE = DATA_DIRECTORY / "weather_mock.csv"
LATTITUDE = 52.1051
LONGITUDE = -3.6680


def _read_power_volume(date: dt.date, period: int) -> pd.DataFrame:
    """Read power volume from mock data.

    This function returns the total power volume per half-hour interval from the
    mock data.

    Args:
        date (datetime.date): Date to consider
        period (int): Half-hour interval (counting from 1 to 48 over the day)

    Returns:
        float: Total power in the grid in this half hour of that day.
    """
    return (
        pd.read_csv(
            MARKET_DATAFILE,
            header=0,
            index_col=["date", "period"],
            parse_dates=True,
            infer_datetime_format=True,
        ).loc[(date, (period + 1) // 2), "volume"]
        / 2.0
    )


def _mock_load_response(date: dt.date, period: int) -> pd.DataFrame:
    """Prepare the mocked data for the load API call.

    This function prepares the data for the BMRS API that would have given the
    forecast load of the grid. It will get fed into the model for prediction
    (among others).

    Args:
        date (datetime.date): Date to consider
        period (int): Half-hour interval (counting from 1 to 48 over the day)

    Returns:
        pd.DataFrame: Load forecast for this period on that day. Actually, this
        is a single number but we provide a bit of additional noise here to more
        closely resemble the API response. It then comes as a single-row
        dataframe which they probably chose in order to later concatenate the
        results for different periods of the day together.
    """
    return pd.read_csv(LOAD_TEMPLATE).assign(
        **{
            "Settlement Date": date,
            "Settlement Period": str(period),
            "Quantity": _read_power_volume(date, period),
        }
    )


def _mock_generation_response(date: dt.date, period: int) -> pd.DataFrame:
    """Prepare the mocked data for the generation API call.

    This function prepares the data for the BMRS API that would have given the
    forecast power generation by resource type (i.e. the predicted kWh of solar
    power, wind power, etc.). We actually don't have mock data for this, so we
    very naively distribute this evenly over the various resources. It will get
    fed into the model for prediction (among others).

    Args:
        date (datetime.date): Date to consider
        period (int): Half-hour interval (counting from 1 to 48 over the day)

    Returns:
        pd.DataFrame: Load forecast for this period on that day with a bit of
        additional noise here to more closely resemble the API response. There
        is one row per resource.
    """
    num_resources = 10
    tmp = pd.read_csv(GENERATION_TEMPLATE).assign(
        **{
            "Settlement Date": date,
            "Settlement Period": str(period),
            "Quantity": _read_power_volume(date, period) / num_resources,
        }
    )
    return tmp


CODE_TO_FUNCTION = {"B1620": _mock_generation_response, "B0620": _mock_load_response}


def mock_elexon_get_bmrs_report(code: str, date: str, period: int) -> pd.DataFrame:
    """Simulate an API to elexon BMRS."""
    return CODE_TO_FUNCTION[code](date, period)


def recursively_formatted(template_obj: Any, **kwargs: Any) -> Any:
    """Recursively format the format strings in a json-like datastructure.

    Given some template_obj (assumed to be a nested list/dict of strings)
    recurses into the datastructure until it finds a str. Such a string will be
    interpreted as format string and formatted with the given kwargs, e.g. if
    your data structure looks something like this

        template_obj = {
            'a': '{placeholder}',
            'b': ['{placeholder}', '{other_placeholder}']
        }

    the result of a call with

        kwargs = {'placeholder': 'c', 'other_placeholder': 'd'}

    would be

        {'a': 'c', 'b': ['c', 'd']}.

    Args:
        template_obj (json-like): Datastructure holding the format strings.
        **kwargs (Any): Passed to `str.format` as kwargs.

    Returns:
        json-like: Equivalent datastructure with all strings formatted.
    """
    # Stopping criterion:
    if isinstance(template_obj, str):
        return template_obj.format(**kwargs)

    # Handle iterables:
    if isinstance(template_obj, dict):
        return {
            key: recursively_formatted(value, **kwargs)
            for key, value in template_obj.items()
        }
    if isinstance(template_obj, list):
        return [recursively_formatted(value, **kwargs) for value in template_obj]

    # Raise if unexpected type:
    raise TypeError(
        "recursively_formatted(...) expects a list, dict, "
        "or str as the first argument. You gave "
        f"{type(template_obj)}."
    )


class MockMetOfficeResponse:
    """Minimal substitute for requests.Response from the met office API call."""

    def __init__(self, date: dt.date) -> None:
        self._date = date
        with open(METOFFICE_TEMPLATE, "r", encoding="utf-8") as file:
            self._json_template = json.loads(file.read())
        self._data = self._read_mock_data(date)

    def _read_mock_data(self, date: dt.date) -> pd.DataFrame:
        """Read mock data and return 3h intervals as Met Office would."""
        return (
            pd.read_csv(
                METOFFICE_DATAFILE,
                header=0,
                infer_datetime_format=True,
                parse_dates=True,
                index_col=["time", "lat", "lon"],
                usecols=[
                    "time",
                    "lat",
                    "lon",
                    "screenTemperature",
                    "windSpeed10m",
                    "significantWeatherCode",
                ],
            )
            .loc(axis=0)[date : date + dt.timedelta(days=2), LATTITUDE, LONGITUDE]
            .droplevel(("lat", "lon"))
            .resample("3h")
            .mean()
        )

    def json(self) -> Dict[str, Any]:
        """Return json as Met Office would."""
        return recursively_formatted(
            self._json_template,
            date=dt.datetime.combine(self._date, dt.time(hour=20)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            date_plus_one=dt.datetime.combine(
                self._date + dt.timedelta(days=1), dt.time(hour=20)
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            lat=LATTITUDE,
            lon=LONGITUDE,
            windspeed=self._data["windSpeed10m"],
            temperature=self._data["screenTemperature"],
            weathercode=self._data["significantWeatherCode"].astype(int),
        )


def mock_met_office_fetch_forecast(date: dt.date) -> MockMetOfficeResponse:
    """Return a mock weather forecast from date."""
    return MockMetOfficeResponse(date)


def mock_mongo_insert_one(*args, **kwargs) -> None:
    """Do not interact with database."""
    pass


sjautobidder.power_integration.power_estimation.mongo_insert_one = mock_mongo_insert_one


def mock_out_api_calls_with(date: dt.date) -> None:
    """Mock out all API calls.

    This function replaces the two functions in the main code that actually
    handle the communication with the API with the mocks from above. It provides
    them with the given date and lets them ignore the given dates when called
    because in the actual code base they will be handed datetime.now() results
    which is not what we want for this task.

    Args:
        date (datetime.date): Fixed date the API calls will simulate.
    """

    sjautobidder.met_office_api.api_interpolation.fetch_forecast = (
        lambda: mock_met_office_fetch_forecast(date)
    )
    # note that date is the argument to mock_out_api_calls_with and NOT unused_date
    sjautobidder.elexon_api.elexon_utils.get_bmrs_report = (
        lambda code, unused_date, period: mock_elexon_get_bmrs_report(
            code, date.strftime("%Y-%m-%d"), period
        )
    )


#################################################################################


def get_price_and_quantity(date: dt.date) -> pd.DataFrame:
    """Predict produced quantity and best price to bid.

    This is the main function of your initial interface to the code. It uses
    whatever the previous group came up with to predict the power production and
    price to bid assuming that today is `date`. You can use it to benchmark the
    quality of the predictions. The team also built an automated bidder and a
    web interface for reporting that you might or might not use in later stages
    of the coding challenge.

    Args:
        date (datetime.date): The fictitious "today".

    Returns:
        pd.DataFrame: A dataframe containing the predicted quantity and price
        over the next bidding interval.
    """
    mock_out_api_calls_with(date)
    return pd.DataFrame(estimate_power(), index=["quantity", "price"]).T


if __name__ == "__main__":
    # Dummy application of the above.
    # Adjust to suit your needs.
    DATE = dt.date(2022, 1, 2)
    print(get_price_and_quantity(DATE))
