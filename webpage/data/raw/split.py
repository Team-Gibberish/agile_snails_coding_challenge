"""splt.py : Convert Data to per-day weather sheets.

Expected data format

split.py
 - /actual/
   - site-generation.dat
 - /forecast/
   - 2020-07-27.csv

site-generation.dat must have the first row containing:
time,solar,wind,demand

"""
import os
import numpy as np
import pandas as pd


def main():

    # Checks to ensure files are present, and in the correct format
    if not os.path.exists("./actual/site-generation.dat"):
        raise FileNotFoundError("Unable to find ./actual/site-generation.dat")
    if not os.path.exists("./forecast/"):
        raise FileNotFoundError("Unable to find ./forecast/")
    with open("actual/site-generation.dat", "r") as realfile:
        if realfile.readline()[:2] == "20":
            raise ValueError("site-generation.dat must contain 'time,solar,wind,demand' on the first line.")

    forecasts = pd.DataFrame(
        columns=[
            "DateTime",
            "SolarPrediction",
            "WindPrediction",
            "TotalGenerated",
            "BuildingPrediction",
            "NetEnergy",
            "Bid Price",
        ]
    )
    print("Loading data files...")
    for file_path in os.listdir("forecast/"):
        if "bids" in file_path:
            continue
        csvFile = pd.read_csv(f"forecast/{file_path}")
        if ['DateTime', 'SolarPrediction', 'WindPrediction', 'TotalGenerated', 'BuildingPrediction', 'NetEnergy', 'Bid Price'] != list(csvFile.columns):
            print(f"Invalid energy data file {file_path}, check data columns.")
            continue
        print(f"ENERGY | {file_path}")
        forecasts = forecasts.append(csvFile)

    # Process site generation
    real = pd.read_csv("actual/site-generation.dat")

    # Rename columns
    real.rename(
        columns={
            "time": "DateTime",
            "solar": "SolarGeneration",
            "wind": "WindGeneration",
            "demand": "BuildingDemand",
        },
        inplace=True,
    )
    # Change date format
    for index, row in real.iterrows():
        real.at[index, "DateTime"] = f'{row["DateTime"]}:00+00:00'

    # Merge real and forecast data
    mframe = forecasts.merge(real, on="DateTime", how="outer")
    mframe.sort_index(inplace=True)

    # Replace -1.0 with nan
    mframe = mframe.replace(-1.0, np.NaN)
    # Ensure demand values are positive
    mframe["BuildingDemand"] = abs(mframe["BuildingDemand"])
    mframe["BuildingPrediction"] = abs(mframe["BuildingPrediction"])

    out_file = open(f'{str(mframe.loc[0, "DateTime"]).split(" ")[0]}.csv', "w")
    out_file.write(
        "DateTime,BuildingPrediction,SolarPrediction,WindPrediction,BuildingDemand,SolarGeneration,WindGeneration\n"
    )
    for index, row in mframe.iterrows():
        if str(row["DateTime"]).split("+")[0][-8:-3] == "23:00":
            out_file.close()
            out_file = open(f'{str(row["DateTime"]).split(" ")[0]}.csv', "w")
            out_file.write(
                "DateTime,BuildingPrediction,SolarPrediction,WindPrediction,BuildingDemand,SolarGeneration,WindGeneration\n"
            )

        out_file.write(
            f'{row["DateTime"]},{row["BuildingPrediction"]},{row["SolarPrediction"]},{row["WindPrediction"]},{row["BuildingDemand"]},{row["SolarGeneration"]},{row["WindGeneration"]}\n'.replace(
                "nan", ""
            )
        )
    out_file.close()
    print("Done!")

if __name__ == "__main__":
    main()
