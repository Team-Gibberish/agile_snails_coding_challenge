import datetime as dt
import json
from typing import Dict, Any

import pandas as pd
import requests

import sjautobidder.elexon_api.elexon_utils
from sjautobidder.power_integration.power_estimation import main as estimate_power

########################### Things related to mocking ###########################
# This following part mocks out API calls for now, so that you can test the code
# without the need to set up API keys and have an internet connection. You can
# safely ignore this part for now.

CODE_TO_FILENAME = {
    "B1620": "dummy_data/generation.csv",
    "B0620": "dummy_data/load.csv",
}
METOFFICE_TEMPLATE = "dummy_data/met_office_template.json"
METOFFICE_DATAFILE = "dummy_data/weather_mock.csv"
LATTITUDE = 52.1051
LONGITUDE = -3.6680


def mock_elexon_get_bmrs_report(code: str, date: str, period: int) -> pd.DataFrame:
    assert code in CODE_TO_FILENAME
    return (
        pd.read_csv(CODE_TO_FILENAME[code])
        .assign(**{"Settlement Date": date})
        .assign(**{"Settlement Period": str(period)})
    )


def recursively_formatted(template_obj: Any, **kwargs: Any) -> Any:
    if isinstance(template_obj, str):
        return template_obj.format(**kwargs)
    if isinstance(template_obj, dict):
        return {
            key: recursively_formatted(value, **kwargs)
            for key, value in template_obj.items()
        }
    return [recursively_formatted(value, **kwargs) for value in template_obj]


class MockResponse:
    def __init__(self, date: dt.date) -> None:
        self._date = date
        with open(METOFFICE_TEMPLATE, "r", encoding="utf-8") as file:
            self._json_template = json.loads(file.read())
        self._data = self._read_mock_data(date)

    def _read_mock_data(self, date: dt.date) -> pd.DataFrame:
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


def mock_met_office_fetch_forecast(date: dt.date) -> MockResponse:
    return MockResponse(date)


def mock_mongo_insert_one(*args, **kwargs) -> None:
    pass


#################################################################################


def get_price_and_quantity(date: dt.date) -> pd.DataFrame:
    # note that date is the argument to get_price_and_quantity and NOT unused_date
    sjautobidder.elexon_api.elexon_utils.get_bmrs_report = (
        lambda code, unused_date, period: mock_elexon_get_bmrs_report(
            code, date.strftime("%Y-%m-%d"), period
        )
    )
    sjautobidder.met_office_api.api_interpolation.fetch_forecast = (
        lambda: mock_met_office_fetch_forecast(date)
    )
    sjautobidder.power_integration.power_estimation.mongo_insert_one = (
        mock_mongo_insert_one
    )
    return pd.DataFrame(estimate_power(), index=["quantity", "price"]).T


if __name__ == "__main__":
    DATE = dt.date(2022, 1, 2)
    print(get_price_and_quantity(DATE))
