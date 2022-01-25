"""Tests for the caching functions.

Todo:
    Tests for intentionally corrupted files.
    Find a way to split up deletion and creation tests without dependence.
"""

import pytest
from sjautobidder.cache import (
    cache_find,
    cache_find_hashed,
    cache_get_hashed,
    cache_remove,
    cache_remove_hashed,
    cache_save_hashed,
    delete_file,
    delete_file_force,
    hash_contents,
    sha1,
    cache_save,
    cache_get,
)


@pytest.mark.parametrize(
    "string, result",
    [
        (
            "Sphinx of black quartz, judge my vow.",
            "77DF869F7E054756BCCE6D85DBB35F01CF3EA24A",
        ),
        (
            "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich",
            "28DABD0F7CE954AC8ADAABD7BB5AB94E4C22358A",
        ),
    ],
)
def test_sha1(string: str, result: str):
    """Test SHA-1 hashing functions."""
    assert sha1(string) == result


@pytest.mark.parametrize(
    "path, result",
    [("tests/resources/random.txt", "40666C55FE60E6001BE004D316531E9F9053EE2C")],
)
def test_hash_contents(path: str, result: str):
    """Test file content hashing functions."""
    assert hash_contents(path) == result


def test_cache_save_load():
    """Test cache saving and loading."""
    object1 = {"Dice? Class�����": 12, "attribute": 123}

    cache_save("test", object1)
    object2 = cache_get("test")

    assert object1 == object2

    cache_save_hashed("test", object1)
    object3 = cache_get_hashed("test")

    assert object1 == object3

    assert cache_find("test") == "Cached/test"
    assert (
        cache_find_hashed("test") == "Cached/A94A8FE5CCB19BA61C4C0873D391E987982FBBD3"
    )

    cache_remove("test")

    assert cache_find("test") is None
    assert (
        cache_find_hashed("test") == "Cached/A94A8FE5CCB19BA61C4C0873D391E987982FBBD3"
    )

    cache_remove_hashed("test")
    assert cache_find_hashed("test") is None

    # Deletion tests
    cache_save("test", object1)
    delete_file(cache_find("test"))
    assert cache_find("test") is None

    cache_save("test", object1)
    delete_file_force(cache_find("test"))
    assert cache_find("test") is None

    # Ensure no errors when deleting a file that does not exist
    delete_file("Cached/test")
    delete_file_force("Cached/test")
