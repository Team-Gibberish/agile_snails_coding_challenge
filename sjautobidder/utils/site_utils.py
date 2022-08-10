# -*- coding: utf-8 -*-
"""
Script containing minor `helper' functions related to site and market operation.

@author: Ben Page
"""

from asyncio.log import logger
import logging
logging.basicConfig(level=logging.INFO, filename='site_utils.log', filemode='w', format='%(asctime)s-%(name)s-%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import datetime as dt
import numpy as np
import pandas as pd
import requests


def get_real_generation():
    """Calculates the real-time solar and wind generation for the Llanwrtyd site.

    Args:
        None

    Returns:
        solar_generation (float) : Current solar generation in kWh.
        wind_generation (float)  : Current wind generation in kWh.
        office_demand (float)    : Current office demand in kWh.
    """

    AIMLAC_CC_MACHINE = "34.72.51.59"
    assert AIMLAC_CC_MACHINE is not None
    host = f"http://{AIMLAC_CC_MACHINE}"

    response = requests.get(url=host + "/sim/llanwrtyd-wells")
    assert len(response.json()) > 0

    message = response.json()['elements']

    solar_labels = ["Solar Generator"]
    wind_labels = ["Wind Generator " + s for s in ['1', '2', '3', '4', 'A', 'B']]
    demand_labels = ["AIMLAC HQ Llanwrtyd Wells", "Llanwrtyd Wells - Computing Centre"]

    solar_generation = 0
    for label in solar_labels:
        value = message[f'Llanwrtyd Wells - {label}']['power']
        solar_generation += value / 1000  # Convert to kWh

    wind_generation = 0
    for label in wind_labels:
        value = message[f'Llanwrtyd Wells - {label}']['power']
        wind_generation += value / 1000  # Convert to kWh

    office_demand = 0
    for label in demand_labels:
        value = message[label]['power']
        office_demand += value / 1000  # Convert to kWh

    return solar_generation, wind_generation, office_demand

def get_clearout():
    """Fetches previous day's clearout prices."""

    start_date = dt.date.today() - dt.timedelta(days=1)
    end_date = dt.date.today() + dt.timedelta(days=1)
    
    AIMLAC_CC_MACHINE = "34.72.51.59"
    assert AIMLAC_CC_MACHINE is not None
    host = f"http://{AIMLAC_CC_MACHINE}"

    g = requests.get(url=host + f"/auction/market/clearout-prices",
                     params=dict(start_date=start_date.isoformat(),
                                 end_date=end_date.isoformat()))

    # Some data should be present!
    assert len(g.json()) > 0

    return g.json()

def get_orders(
    date: (list, str),
    period: (list, int),
    net_generation: (list, float),
    sys_price: (list, float),
):
    """Calculates bid quantity and bid direction and returns resulting market
       order.

    Args:
        date (list,str)             : Date or list of dates for the market bid.
        period (list,int)           : Period or list of periods for the market
                                      bid.
        net_generation (list,float) : Predicted net generation in KWh.
        sys_price (list,float)      : Predicted market (system) price in
                                      GBP/MWh.

    Returns:
        orders (list(dict),dict) : Dict or list of dicts containing market bids.
    """

    assert isinstance(date, (list, str, np.ndarray))
    assert isinstance(period, (list, int, np.ndarray))
    assert isinstance(net_generation, (list, float, np.ndarray))
    assert isinstance(sys_price, (list, float, np.ndarray))

    # Check for single market bid
    if not all(
        isinstance(v, (list, np.ndarray))
        for v in [date, period, net_generation, sys_price]
    ):
        direction = "SELL" if net_generation >= 0 else "BUY"

        if direction == "BUY":
            sys_price = 150  # Buy at National Grid rate of 15p/kWh

        orders = {
            "applying_date": date,
            "hour_ID": period,
            "type": direction,
            "volume": round(abs(net_generation) / 1000, 3),  # Convert to MWh
            "price": round(sys_price, 2),
        }
    else:
        orders = []
        for pos, _ in enumerate(date):

            direction = "SELL" if net_generation[pos] >= 0 else "BUY"

            if direction == "BUY":
                sys_price[pos] = 150  # Buy at National Grid rate of 15p/kWh

            order = {
                "applying_date": date[pos],
                "hour_ID": int(period[pos]),
                "type": direction,
                "volume": round(abs(net_generation[pos]) / 1000, 3),  # Convert to MWh
                "price": round(sys_price[pos], 2),
            }
            orders.append(order)

    return orders


def submit_orders(orders):
    """Submits orders via the site API"""

    AIMLAC_CC_MACHINE = "34.72.51.59"
    assert AIMLAC_CC_MACHINE is not None
    host = f"http://{AIMLAC_CC_MACHINE}"
    key = "AgileSnails8394587201"

    message = requests.post(
        url=host + "/auction/bidding/set", json={"key": key, "orders": orders}
    )
    logging.info(message.content)
    data = message.json()
    logging.info("Posting bids:")
    logging.info("POST JSON reply:", data)
    assert data["accepted"] >= 1
    assert data["message"] == ""

    logging.info("done.")


def get_grid_intensity(date: (str), period=None):
    """Fetches the current carbon intensity of the National Grid.

    Args:
        date (str)   : Date in YYYY-MM-DD format.
        period (int) : Market period (default is None).

    Returns:
        str, np.ndarray : Date in <YYYY-MM-DD>T<HH:mm>Z format.
        int, np.ndarray : Carbon intensity in g/kWh.
        str, np.ndarray : Carbon indensity index.
    """

    assert isinstance(date, str)

    if period is not None:
        assert isinstance(period, int)
        assert 0 < period <= 50

    if period is None:
        url = f"https://api.carbonintensity.org.uk/intensity/date/{date}"
    else:
        url = f"https://api.carbonintensity.org.uk/intensity/date/{date}/{period}"

    response = requests.get(url)
    data = response.json()['data']

    intensity = []
    index = []
    timestamp = []

    for record in data:
        intensity.append(record['intensity']['actual'])
        index.append(record['intensity']['index'])
        timestamp.append(record['from'])

    if period is None:
        return np.asarray(timestamp), np.asarray(intensity), np.asarray(index)
    return timestamp[0], intensity[0], index[0]


def to_csv(data: dict, filename=None):
    """Dumps data dict to csv.

    Args:
        data (dict)    : dict object containing forecast data
        filename (str) : string containing filename (without extension) to
                         which the data is written. (Default is None).
    Returns:
        None
    """

    assert isinstance(data, (dict, list))

    if filename is None:
        filename = dt.datetime.strftime(dt.datetime.now(), "%Y-%m-%d")
    else:
        assert isinstance(filename, str)

    table = pd.DataFrame.from_dict(data)
    table.to_csv(filename + ".csv", index=False)

if __name__ == "__main__":
    logging.info(get_real_generation())
