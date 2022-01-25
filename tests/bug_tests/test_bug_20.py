import pytest
from sjautobidder.elexon_api.elexon_utils import df_unstacker, get_bmrs_report


@pytest.mark.parametrize(
    "date",
    ["2021-05-17", "2021-01-21", "2020-07-11", "2020-01-01"],
)
def test_equal_record(date):
    """Check that df_unstacker() successfully unstacks dataframes with equal
    records in the target column."""

    code = "B1770"  # Problem report

    data = get_bmrs_report(code, date, 1)  # Fetch BMRS report

    anchors = ["SettlementDate", "SettlementPeriod"]
    label = "PriceCategory"
    target = "ImbalancePriceAmount"

    new_data = df_unstacker(data, anchors, label, target)

    """The unstacked record should be a 4 column by 1 row data frame containing
    two label columns, `Insufficient balance` and `Excess balance`."""

    assert len(new_data) == 1
    assert len(new_data.columns) == 4
    assert "Insufficient balance" in list(new_data.columns)
    assert "Excess balance" in list(new_data.columns)
