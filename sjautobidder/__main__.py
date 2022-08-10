"""Power prediction and automatic bidding application."""

import datetime as dt
import time
import numpy as np

import sjautobidder.utils.site_utils as site_utils
import sjautobidder.utils.mongo_utils as mongo_utils
import sjautobidder.power_integration.power_estimation as power_estimation


def align_time():
    """Completes when the current time aligns to the nearest mintue with the
    start of the next market period."""

    current_minute = dt.datetime.now().minute

    time_aligned = bool(current_minute in (0, 30))

    runtime = 0  # Count number of seconds elapsed
    while time_aligned is False:
        time.sleep(1)

        current_minute = dt.datetime.now().minute
        time_aligned = bool(current_minute in (0, 30))
        runtime += 1

        if runtime > 1860:
            raise Exception("Could not align time. Runtime exceeded 31 mins.")


def standard_time(timestamp: dt.datetime) -> str:
    """Rounds a timestamp to the nearest 30-minute period.

    Args:
        timestamp (dt.datetime) : Timestamp

    Returns
        (str) : Timestamp in format '<YYYY-MM-DD> HH:mm'
    """

    date = timestamp.date()

    hour = timestamp.hour
    minute = timestamp.minute

    return f"{date} {hour:02}:{(minute//30)*30:02}"
    

def main():
    """Start the autobidder."""

    tformat = "%Y-%m-%d %H:%M:%S"

    print("Agile Snails Autobidder started!")
    print("Use Ctrl-C to stop.")

    solar_generation, wind_generation, office_demand = site_utils.get_real_generation()
    timestamp = standard_time(dt.datetime.now())

    mongo_utils.mongo_insert_one("site-generation", {
        "timestamp": timestamp,
        "solar_generation": solar_generation,
        "wind_generation": wind_generation,
        "office_demand": office_demand
    })

    # 'Count in' the internal clock
    # Only starts running the main program at the start of a half-hour interval
    print("Aligning clock...")
    align_time()

    while True:
        print(f"{'TIME'.center(20)}| STATUS")
        
        solar_generation, wind_generation, office_demand = site_utils.get_real_generation()
        timestamp = standard_time(dt.datetime.now())

        mongo_utils.mongo_insert_one("site-generation", {
            "timestamp": timestamp,
            "solar_generation": solar_generation,
            "wind_generation": wind_generation,
            "office_demand": office_demand
        })

        with open("webpage/data/site-generation.dat", 'a') as fout:
            fout.write(f"{timestamp},{solar_generation},{wind_generation},{office_demand}\n")

        # Fetch and submit orders
        if int(time.strftime("%H")) == 7 and int(time.strftime("%M")) < 5:
            print(f"{dt.datetime.now().strftime(tformat)} | Submitting bids...")
            # Update MongoDB with newest forecast
            net_energy, price_prediction = power_estimation.main()

            # Fetch market orders
            current_day = dt.datetime.now().date()
            dates = 24 * [current_day + dt.timedelta(days=1)]

            str_dates = [date.strftime("%Y-%m-%d") for date in dates]
            hour_id = np.arange(1,25)

            # Fetch orders for each hour
            orders = site_utils.get_orders(
                str_dates,
                hour_id,
                (net_energy + np.roll(net_energy, -1))[::2],
                price_prediction[::2]
            )
            site_utils.to_csv(
                orders,
                filename=f"webpage/data/{dt.datetime.now().strftime('%Y-%m-%d')}-bids"
            )
            # Submit orders
            try:
                site_utils.submit_orders(orders)
            except ValueError:
                print("Could not submit bids! Continuing...")

            # Fetch  previous day's orders

            prev_orders = site_utils.get_clearout()
            site_utils.to_csv(prev_orders, filename=f"webpage/data/{dt.date.today()}-real")
            
        for _ in range(26):
            print(f"{dt.datetime.now().strftime(tformat)} |\tsj running")
            time.sleep(60)

        align_time()  # Adjust for clock jitter


if __name__ == "__main__":
    main()
