"""File-based caching system.

Implemented with pickle.
@author Iwan Mitchell
"""

import os
import stat
import hashlib
import pickle
from typing import Optional


class CacheError(Exception):
    """An error encountered while trying to read or write from cache."""


def hash_contents(path: str) -> str:
    """Hash the contents of a file using the SHA-1 algorithm.

    Args:
        path (str): Path to the file to be hashed

    Raises:
        FileNotFoundError: Raised when the given file does not exist.

    Returns:
        str: A 40 digit long hexadecimal string that represents the
            contents of the given file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError

    hasher = hashlib.sha1()
    block_sz = 8192
    with open(path, "rb") as file:
        buf = file.read(block_sz)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file.read(block_sz)
    return str(hasher.hexdigest()).upper()


def sha1(string: str) -> str:
    """Get the SHA-1 hash of the provided string in UTF-8.

    Args:
        string (str): String to hash

    Returns:
        str: A 40 digit long hexadecimal string that represents the
            contents of the given file.
    """
    return str(hashlib.sha1(string.encode()).hexdigest()).upper()


def cache_create() -> None:
    """Create a cache."""
    if not os.path.exists("Cached/"):
        os.mkdir("Cached")


def cache_find(item: str) -> Optional[str]:
    """Return the path of a cached file object.

    Args:
        item (str): A string identifier of a potentially cached object.

    Returns:
        Optional[str]: The path of a cached file stored under the string identifier.
            Will return `None` if no file is found.
    """
    item = str(item)
    cache = "Cached/" + item

    if os.path.exists(cache):
        return cache

    return None


def cache_find_hashed(item: str) -> Optional[str]:
    """Return the path of a hashed cached file object.

    Args:
        item (str): A string identifier of a potentially cached object.
            This will be hashed to a safe-to-store value and has no limit on size.

    Returns:
        Optional[str]: The path of a cached file stored under the hashed
            string identifier. Will return `None` if no file is found.
    """
    return cache_find(sha1(item))


def cache_get(item: str) -> Optional[object]:
    """Get an object with the string identifier from the cache.

    Args:
        item (str): A string identifier of a potentially cached object.

    Raises:
        CacheReadError: A lower error raised by `open` or `pickle.load`

    Returns:
        Optional[object]: Object that was cached with the given identifier.
            Will return `None` if no object is found.
    """
    item = str(item)
    cache = cache_find(item)

    # cache_find() will return none if the cache does not exist
    # the returned location is guaranteed to exist, so no point checking again.

    if cache is not None:
        try:
            cached = pickle.load(open(cache, "rb"))
        except EOFError:
            # Cache file is corrupted, so act like it does not exist.
            # We do not delete the cache file in case the user wants
            # to recover the file.
            return None
        except Exception as ex:
            raise CacheError(ex)
        return cached
    return None


def cache_get_hashed(item: str) -> object:
    """Get an object with the hashed string identifier from the cache.

    Args:
        item (str): A string identifier of a potentially cached object.
            This will be hashed to a safe-to-store value and has no limit on size.

    Raises:
        CacheReadError: A lower error raised by `open` or `pickle.load`

    Returns:
        Optional[object]: Object that was cached with the given identifier.
            Will return `None` if no object is found.
    """
    return cache_get(sha1(item))


def cache_save(item: str, obj: object) -> None:
    """Save an item to the cache under the given string identifier.

    Args:
        item (str): String identifier to save the object under.
        obj (object): Object to save to cache.

    Raises:
        CacheError: An error thrown if any issues were encountered trying to
            serialize or save the object to disk.
    """
    item = str(item)
    cache = "Cached/" + item

    try:
        cache_create()
        pickle.dump(obj, open(cache, "wb"))
    except Exception as ex:
        raise CacheError(ex)


def cache_save_hashed(item: str, obj: object) -> None:
    """Save an item to the cache with a hashed string identifier.

    Args:
        item (str): A string identifier of a potentially cached object.
            This will be hashed to a safe-to-store value and has no limit on size.
        obj (object): Object to save to cache.

    Raises:
        CacheError: An error thrown if any issues were encountered trying to
            serialize or save the object to disk.
    """
    cache_save(sha1(item), obj)


def cache_remove(item: str) -> None:
    """Remove an object from the cache with the provided id.

    Args:
        item (str): String identifier of the object to delete.
    """
    item = str(item)
    cache = "Cached/" + item

    if os.path.exists(cache):
        delete_file(cache)


def cache_remove_hashed(item: str) -> None:
    """Remove an object from the cache with the provided id.

    Args:
        item (str): A string identifier of a potentially cached object.
            This will be hashed to a safe-to-store value and has no limit on size.
    """
    cache_remove(sha1(item))


def delete_file(file: str) -> None:
    """Delete the provided file. Does not delete folders.

    Args:
        file (str): Path to file for deletion.
    """
    if not os.path.exists(file):
        # Files does not exist
        return

    os.remove(file)


def delete_file_force(file: str) -> None:
    """Delete the provided file, while ignoring read-only markers.

    Does not delete folders.
    """
    if not os.path.exists(file):
        # Files does not exist
        return

    # mark file as writeable. This should allow deleting read-only files.
    os.chmod(file, stat.S_IWRITE)
    os.remove(file)
