# -*- coding: utf-8 -*-
"""Functions to collect energy market data from Elexon.

@author: jadot-bp
"""

import sjautobidder.elexon_api.elexon_utils as elexon_utils


def main():
    """Display some examples of functions from elexon_utils.py."""
    date = "2021-05-05"     # Date must be in YYYY-MM-DD format
    period = 12             # Period must be between 1-48 (inclusive)
    code = "B1440"          # BMRS code for wind and solar forecast

    print(f"Report: {code}\n")
    print(elexon_utils.get_bmrs_report(code, date, period))

    print("\nSupported Codes:\n")
    print(elexon_utils.CODE_DESCRIPTORS)

    from_date = "2021-05-01"
    to_date = "2021-05-10"

    print("\nDerived System Data Report:\n")
    print(elexon_utils.get_dersys_data(from_date, to_date, period))

    code = "B0620"          # BMRS code for Day-Ahead load forecast

    print(f"\nBMRS {code} Data series:\n")
    print(elexon_utils.get_bmrs_series(code, from_date, to_date))

    code = "B1620"          # BMRS code for generation per fuel type

    data = elexon_utils.get_bmrs_series(code, from_date, to_date)
    anchors = ["Settlement Date", "Settlement Period"]
    label = "Power System Resource  Type"
    target = "Quantity"

    print(f"\nBMRS {code} Unpacked:\n")
    print(elexon_utils.df_unstacker(data, anchors, label, target))


if __name__ == "__main__":
    main()
