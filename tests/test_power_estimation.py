"""Tests for the power estimation."""

import pandas as pd
from sjautobidder.power_integration.power_estimation import main as estimate_power
import sjautobidder.power_integration.power_estimation as pe

def _mock_mongo_insert_one(*args, **kwargs) -> None:
    pass

def test_power_estimation():
    pe.mongo_insert_one = _mock_mongo_insert_one

    res = pd.DataFrame(estimate_power(), index=["quantity", "price"]).T

    assert res.shape == (49,2)
