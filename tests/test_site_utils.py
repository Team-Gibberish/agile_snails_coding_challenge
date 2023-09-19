"""Tests for site_utils.py."""

from sjautobidder.utils.site_utils import get_real_generation

def test_get_real_generation():
    """This can only work after uploading to the google cloud shit
    """
    solar, wind, office = get_real_generation()

    assert isinstance(solar, float)
    assert isinstance(wind, float)
    assert isinstance(office, float)
