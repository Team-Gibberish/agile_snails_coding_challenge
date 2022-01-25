from sjautobidder.elexon_api.elexon_utils import get_bmrs_report, df_unstacker


def test_stacked_record():
    """Test for bug #19: df_unstacker() fails on duplicated records."""

    bmrs_code = "B1620"  # BMRS fuel breakdown code

    expected_len = 11    # There should be 11 records, one for each fuel type

    # Test for bugged record
    date = "2020-02-10"
    period = 29

    data = get_bmrs_report(bmrs_code, date, period)

    assert len(data) == expected_len        # Check for bugged record

    # Check that a correct record returns expected length
    date = "2020-02-10"
    period = 30

    data = get_bmrs_report(bmrs_code, date, period)

    assert len(data) == expected_len


def test_df_unstacker_on_bug_19():
    """Test df_unstacker() with a duplicated record."""

    bmrs_code = "B1620"

    date = "2020-02-10"

    anchors = ["Settlement Date", "Settlement Period"]
    label = "Power System Resource  Type"
    target = "Quantity"

    # Check that unduplicated record unstacks successfully
    period = 30

    data = get_bmrs_report(bmrs_code, date, period)
    unstacked_data = df_unstacker(data, anchors, label, target)

    assert len(unstacked_data) == 1

    # Test for failure in df_unstacker()
    period = 29

    data = get_bmrs_report(bmrs_code, date, period)
    unstacked_data = df_unstacker(data, anchors, label, target)

    assert len(unstacked_data) == 1
