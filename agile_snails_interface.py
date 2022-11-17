import datetime as dt
import json

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
METOFFICE_FILENAME = {"default": "dummy_data/met_office.json"}


def mock_elexon_get_bmrs_report(code: str, date: str, period: int) -> pd.DataFrame:
    assert code in CODE_TO_FILENAME
    return (
        pd.read_csv(CODE_TO_FILENAME[code])
        .assign(**{"Settlement Date": date})
        .assign(**{"Settlement Period": str(period)})
    )


class MockResponse:
    def __init__(self, json_content: str) -> None:
        self._json_str = json_content

    def json(self) -> None:
        return json.loads(self._json_str)


def mock_met_office_fetch_forecast(date: dt.date) -> MockResponse:
    METOFFICE_FILENAME.setdefault(date, METOFFICE_FILENAME["default"])
    with open(METOFFICE_FILENAME[date], "r", encoding="utf-8") as file:
        return MockResponse(file.read())


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
