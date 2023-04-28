# -*- coding: utf-8 -*-
"""
Script to calculate energy generation from Solar and Wind instillations,
consumption from building demand and collate into an overall prediction
for net energy generation for half hour timesteps in next 23:00-23:00
interval. Results and forecast are written to MongoDB in the
'energy_prediction' collection.

@author: Matt
"""

import logging
logger = logging.getLogger(__name__)

import datetime as dt
import numpy as np

from sjautobidder.wind_power.wind_utils import get_wind_prediction
from sjautobidder.solar_power.solar_power import get_solar_prediction
from sjautobidder.building_demand.energy_demand import get_energy_demand
from sjautobidder.met_office_api.api_interpolation import get_forecast
from sjautobidder.autobidder.autobidder_utils import get_price_forecast
from sjautobidder.utils.mongo_utils import mongo_insert_one
from sjautobidder.utils.panda_utils import df_to_dict

@profile
def main():
    #estimate_price
    # Fetch forecast from MetOffice API
    forecast = get_forecast()
    # Solar prediction (kW)
    solar_prediction = get_solar_prediction()
    datetimes = solar_prediction.index
    # Wind prediction (kW)
    wind_prediction = get_wind_prediction()
    # Building demand prediction (kW)
    building_demand = get_energy_demand()
    # Total energy produced
    energy_generated = np.asarray(solar_prediction) + np.asarray(
        wind_prediction["WindPower"]
    )
    energy_consumption = np.append(
        np.asarray(building_demand["Total demand"]),
        np.asarray(building_demand["Total demand"])[-1],
    )
    net_energy = energy_generated - energy_consumption
    # Market price prediction (GBP/MWh)
    price_prediction = get_price_forecast()
    # Collect results
    energy_predictions = {}
    energy_predictions["DateTime"] = datetimes.tolist()
    energy_predictions["SolarPrediction"] = solar_prediction.tolist()
    energy_predictions["WindPrediction"] = wind_prediction["WindPower"].tolist()
    energy_predictions["TotalGenerated"] = energy_generated.tolist()
    energy_predictions["BuildingPrediction"] = energy_consumption.tolist()
    energy_predictions["NetEnergy"] = net_energy.tolist()
    energy_predictions["Bid Price"] = price_prediction
    # Write to csv
    # to_csv(energy_predictions, filename=f"webpage/data/{dt.datetime.now().strftime('%Y-%m-%d')}")
    # to_csv(orders, filename=f"{dt.datetime.now().strftime('%Y-%m-%d')}-bids")
    
    logging.info("Writing power estimations to mongoDB:")

    # Write to mongodb
    datetime_calculated = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    mongo_data = {
        "datetime_calculated": datetime_calculated,
        "predictions": energy_predictions,
        "forecast": df_to_dict(forecast),
    }
    mongo_insert_one("energy_predictions", mongo_data)  # Returns True if successful
    logging.info("Writing power estimations successful")

    return net_energy, price_prediction


if __name__ == "__main__":
    main()
