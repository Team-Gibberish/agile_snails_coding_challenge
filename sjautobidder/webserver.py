"""HTTP Server for the reporting interface.

This is a basic webserver, and aims to simply host the files needed to view the
generated report files in a clear format. This webpage takes no input in from
the user.

Due to the small nature of the webapp, along with minimal files, each file is
linked up manually to reduce the amount of attack vectors that may be attempted
on the webserver. Although these steps have been taken, it is recommended to not
expose this website to external networks.
"""
# pylint: disable=global-statement

import calendar
import datetime as dt
import os
from typing import Dict, List, Union
from flask.helpers import send_from_directory

import numpy as np
import pandas as pd
import requests
from flask import Flask, jsonify, make_response
from flask.wrappers import Response
from flask_cors import CORS

from cache import cache_get_hashed, cache_save_hashed

application = Flask(__name__)

# https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
CORS(application, support_credentials=True)

# We use a global 'cache' to store pages in RAM and prevent having to read
# the file all the time. This is a global variable so we're able to use it
# in multiple functions. This shouldn't cause a race issue, since even if
# two functions are writing to the cache at the same time, the stored data
# is deterministic.
CACHE: Dict[str, str] = {}

# Debug data
BID_DATA = {}
ENERGY_DATA = {}
DATES = {}


def get_location() -> str:
    """Get the absolute path of the webpage files.

    Returns:
        str: Absolute path of the folder containing webpage files.
    """
    if "SJSITE" in os.environ:
        if os.path.isdir(os.environ["SJSITE"]):
            return os.environ["SJSITE"]
    return os.path.abspath(os.path.curdir) + "/webpage/"


def get_text_file(path: str) -> str:
    """Obtain a webpage file.

     This makes use of a cache to ensure the filesystem is not hit more than
     once.

    Args:
        path (str): Path to the webpage file. Cannot include .. or begin with /.

    Raises:
        ValueError: Raised if the given path contains '..' or begins with '/'

    Returns:
        str: Webpage file contents
    """
    global CACHE

    if ".." in path:
        raise ValueError("Cannot import files containing '..' in the path.")
    if path.strip()[0] == "/":
        raise ValueError("Cannot import files starting with '/'")

    if path in CACHE:
        result = CACHE.get(path)
        if isinstance(result, str):
            return result

    with open(f"{get_location()}{path}", "r", encoding="UTF-8") as file:
        file_contents = "\n".join(file.readlines())
        CACHE[path] = file_contents
    return file_contents


###########################################################################
############################# Webpage Frontend ############################
###########################################################################


# ---------- HTML ---------- #


def setup():
    """Webserver setup, such as managing database connections and loading data."""
    load_data()
    # compile_month_data()
    # print(carbon_rate_month("2021-08"))

    # print(ENERGY_DATA["2021-08"])


application.before_first_request(setup)


@application.route("/", methods=["GET"])
def index_page() -> Response:
    """Website index page."""
    response = make_response(get_text_file("index.html"))
    return response


@application.route("/index.html/<date>", methods=["GET"])
def history_date(date) -> Response:
    """Website history page. Date value is handled on the webpage"""
    return index_page()


# ------- Javascript ------- #

@application.route("/js/lib.js", methods=["GET"])
def js_lib() -> Response:
    """Website javascript library."""
    response = make_response(get_text_file("js/lib.js"))
    response.headers["Content-Type"] = "text/javascript"
    return response


@application.route("/js/index.js", methods=["GET"])
def js_history() -> Response:
    """Website history javascript."""
    response = make_response(get_text_file("js/index.js"))
    response.headers["Content-Type"] = "text/javascript"
    return response


# ----------- CSS ---------- #


@application.route("/css/style.css", methods=["GET"])
def css_style() -> Response:
    """Website javascript library."""
    response = make_response(get_text_file("css/style.css"))
    response.headers["Content-Type"] = "text/css"
    return response


# --------- Assets --------- #


@application.route("/favicon.ico", methods=["GET"])
def icon_favicon() -> Response:
    """Website favicon."""
    file_data: bytes
    with open(f"{get_location()}img/favicon.ico", "rb") as file:
        file_data = file.read()
    response = make_response(file_data)
    response.headers["Content-Type"] = "image/ico"
    return response


# ------ API Endpoint ------ #

@application.route("/api/downloads/energy/<date>", methods=["GET"])
def download_energy(date: str) -> Response:
    # Ensure date exists
    data = get_energy_data(date)
    if data is None:
        print("data is none")
        response = Response("", 404)
    else:
        print("Serving file "+f"{get_location()}data/"+ f"{date}.csv")
        response = send_from_directory(f"{get_location()}data/", f"{date}.csv")
    return response


@application.route("/api/downloads/bids/<date>", methods=["GET"])
def download_bids(date: str) -> Response:
    # Ensure date exists
    print(date)
    data = get_bid_data(date)
    if data is None:
        response = Response("", 404)
    else:
        response = send_from_directory(f"{get_location()}data/", f"{date}-bids.csv")
    return response


@application.route("/api/report/<date>", methods=["GET"])
def get_report(date: str) -> Response:
    """Energy data report."""
    data = get_energy_data(date)
    if data is None:
        response = Response("", 404)
    else:
        response = jsonify(data)
    return response


@application.route("/api/dates", methods=["GET"])
def get_dates() -> Response:
    """Dates with reporting data."""
    data = get_data_dates()
    if data is None:
        response = Response("", 404)
    else:
        response = jsonify(data)
    return response


@application.route("/api/bids/<date>", methods=["GET"])
def get_bids(date: str) -> Response:
    """Bid dates"""
    data = get_bid_data(date)
    if data is None:
        response = Response("", 404)
    else:
        response = jsonify(data)
    return response


def get_energy_data(date: str) -> Union[Dict, None]:
    global ENERGY_DATA
    if date not in ENERGY_DATA:
        return None
    return ENERGY_DATA[date]


def get_data_dates() -> Union[Dict, None]:
    global DATES
    return DATES


def get_bid_data(date: str) -> Union[Dict, None]:
    global BID_DATA
    if date not in BID_DATA:
        return None
    return BID_DATA[date]


###########################################################################
####################### Data loading and formatting #######################
###########################################################################


def load_data() -> None:
    """Load data from csv files and store into global variables.
    This should be replaced with a database connection."""
    global DATES
    global BID_DATA
    global ENERGY_DATA

    # ----------------------------------------------------------------
    # Load data from csv files, and transform into data format.

    # iterate csv files in folder
    dates = {}
    folder = f"{get_location()}/data/"
    for file in os.listdir(folder):
        date = file[:10]
        isbid = file[-8:][:-4] == "bids"
        if date[:2] != "20" or len(date) != 10 or len(date.split("-")) != 3:
            continue

        # Append date to data
        month_key = dates.setdefault(date[:-3], set())
        month_key.add(date[-2:])
        dates[date[:-3]] = month_key

        print(f"{'BID' if isbid else 'ENERGY'} \t| {date}")

        data = pd.read_csv(folder + file)
        if isbid:
            BID_DATA[date] = {}
            BID_DATA[date]["data"] = data.values.tolist()
        else:
            store_energy_day(data, date)

    # sort dates
    for month in dates:
        lst = list(dates[month])
        lst.sort()
        dates[month] = lst

    DATES = dates

    last_day = None

    # Collate and create Month overviews
    for month in dates:
        print(f"COLLATING\t| {month}")
        month_start = dt.datetime(
            int(month.split("-")[0]), int(month.split("-")[1]), 1, 0, 0, 0, 0
        )
        _, days = calendar.monthrange(month_start.year, month_start.month)

        # Prepare data frame for all data
        month_data = pd.DataFrame(
            np.zeros((days * 48, 7)),
            columns=[
                "DateTime",
                "BuildingPrediction",
                "SolarPrediction",
                "WindPrediction",
                "BuildingDemand",
                "SolarGeneration",
                "WindGeneration",
            ],
        )
        # set 0 to NaN
        month_data[month_data == 0] = None

        tformat = "%Y-%m-%d %H:%M:%S"

        # Create date times for the month
        for index in range(days * 48):
            minutes_to_add = index * 30
            temp_time = month_start + dt.timedelta(minutes=minutes_to_add)
            month_data.loc[index, ("DateTime")] = f"{temp_time.strftime(tformat)}+00:00"

        # Edge case; check to see if last day of previous month exists. This is
        # because records that begin on '2021-08-31' will contain the majority
        # of records for '2021-09-01'
        # if last_day is not None:
        #     print(f"lastDay:{last_day}")
        #     for row_index, row in pd.DataFrame(ENERGY_DATA[last_day.strftime("%Y-%m-%d")]["data"], columns=month_data.columns).iterrows():
        #         # skip first two rows
        #         if int(row_index) < 2:
        #             continue
        #         print(month_data["DateTime"][month_data["DateTime"] == row["DateTime"]])
        #         print(row_index)
        #         month_data.to_csv("test.csv")
        #         print(row["DateTime"])
        #         icol = month_data["DateTime"][month_data["DateTime"] == row["DateTime"]].index[0]
        #         for column in month_data.columns:
        #             month_data.loc[icol, str(column)] = row[column]

        # For each day, read data and combine
        for day in dates[month]:
            dayDateTime = dt.datetime.strptime(f"{month}-{day}", "%Y-%m-%d")
            day_data = pd.DataFrame(
                ENERGY_DATA[f"{month}-{day}"]["data"], columns=month_data.columns
            )
            day_data = day_data.astype(
                {
                    "DateTime": str,
                    "BuildingPrediction": float,
                    "SolarPrediction": float,
                    "WindPrediction": float,
                    "BuildingDemand": float,
                    "SolarGeneration": float,
                    "WindGeneration": float,
                }
            )

            day_data.set_index("DateTime").astype(str)
            month_data.set_index("DateTime").astype(str)
            # ? Tried to merge, not sure why it doesn't work...
            # cc = month_data.merge(day_data, how="outer")

            # First two records of the first day of the month is actually from the previous month.
            if len(day_data["DateTime"]) == 1:
                continue

            # Find first day of current data sheet. If the day is the first of the month, ignore the first two rows (since they'll be last month's data.)
            dayOffset = 2 if month_start == dayDateTime else 0
            indexes = month_data["DateTime"][month_data["DateTime"] == day_data.loc[dayOffset, "DateTime"]]

            icol = indexes.index[0]
            for index in range(0, len(day_data)-dayOffset):
                if (index + icol) >= len(month_data):
                    break
                if month_data.loc[index + icol, "DateTime"] == day_data.loc[index + dayOffset, "DateTime"]:
                    for column in month_data.columns:
                        month_data.loc[index + icol, str(column)] = day_data.loc[index + dayOffset, str(column)]
                        # print(day_data.loc[index, str(column)])

        month_data.to_csv(f"{get_location()}data/{month}.csv", index=False)
        store_energy_month(month_data, month)


def store_energy_day(data: pd.DataFrame, date_key: str) -> None:
    """Save energy data to the page cache. Should be replaced by a database.

    Args:
        data (pd.DataFrame): Dataframe containing energy data
        dateKey (str): Date in ISO format (2020-06-27)
    """
    ENERGY_DATA[date_key] = {}
    # Store values as a python list and ensure nan is changed to None.
    values = []
    for row in data.values:
        row_data = []
        row_data.append(row[0])
        for value in list(row[1:]):
            row_data.append(None if np.isnan(value) else value)
        values.append(row_data)
    ENERGY_DATA[date_key]["data"] = values

    # One day actually has two days, get carbon rate for today and yesterday
    date_previous = (dt.datetime.strptime(date_key, "%Y-%m-%d") - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    ENERGY_DATA[date_key]["carbonRate"] = {date_key: carbon_rate_day(date_key), date_previous: carbon_rate_day(date_previous)}


def store_energy_month(data: pd.DataFrame, date_key: str) -> None:
    """Save energy data to the page cache. Should be replaced by a database.

    Args:
        data (pd.DataFrame): Dataframe containing energy data
        dateKey (str): Month in ISO format (2020-06)
    """
    ENERGY_DATA[date_key] = {}
    # Store values as a python list and ensure nan is changed to None.
    values = []
    for row in data.values:
        row_data = []
        row_data.append(row[0])
        for value in list(row[1:]):
            row_data.append(None if np.isnan(value) else value)
        values.append(row_data)
    ENERGY_DATA[date_key]["data"] = values
    ENERGY_DATA[date_key]["carbonRate"] = carbon_rate_month(date_key)


# ----- CO2 Calculation ---- #


def carbon_rate_day(date: str) -> float:
    """Obtain the carbon rate of the given ISO date

    Args:
        str (date): ISO Date (2021-06-27)

    Returns:
        float: co2/kwh for each unit of energy. -1 represents days with no data.
    """
    co2 = 0.0

    # Check cache
    savedCo2 = cache_get_hashed(f"Co2-{date}")
    if savedCo2 is not None and isinstance(savedCo2, float):
        return savedCo2

    # Request co2 values from external api
    try:
        response = requests.get(
            f"https://api.carbonintensity.org.uk/intensity/date/{date}"
        )

        # Ensure response is valid
        if response.status_code != 200:
            print(
                f"ERROR {response.status_code}: Failed to obtain co2 measurement of {date}. "
            )
            return -1

        request_data = response.json()["data"]

        # Average out results for entire day
        for segment in request_data:
            co2 += segment["intensity"]["forecast"]
        co2 /= len(request_data)

        cache_save_hashed(f"Co2-{date}", co2)
        return co2
    except:
        print(f"ERROR: Failed to obtain co2 measurement of {date}. ")
        return -1


def carbon_rate_month(date: str) -> Dict[str, float]:
    """Obtain the carbon rate of very day in the given ISO month

    Args:
        date (str): ISO Month (2021-06)

    Returns:
        Dict[str, float]: A list of co2/kwh values. -1 represents days with no data.
    """
    # Monthstart
    month_start = dt.datetime(
        int(date.split("-")[0]), int(date.split("-")[1]), 1, 0, 0, 0, 0
    )

    # Monthend
    _, days = calendar.monthrange(month_start.year, month_start.month)

    co2: Dict[str, float] = {}
    for day in range(0, days):
        day_date = f"{date}-{day+1:02}"
        co2[day_date] = carbon_rate_day(day_date)
    return co2


if __name__ == "__main__":
    print(get_location())
    application.run("127.0.0.1", 80)
