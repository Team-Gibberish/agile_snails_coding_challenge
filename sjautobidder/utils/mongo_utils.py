"""Utilities to be used for interacting with the MongoDB database."""

from pymongo import MongoClient

HOST = "projectdata.sabco.mongodb.net"
DATABASE_NAME = "CodingChallenge"
USERNAME = "agilesnails"
PASSWORD = "agilesnails"

def setup_client() -> MongoClient:
    """Sets up a MongoDB connection object.

    Returns:
        client (MongoClient)
    """
    connection_string = f"mongodb+srv://{USERNAME}:{PASSWORD}@{HOST}"
    client = MongoClient(connection_string)
    return client


def mongo_insert_one(collection_name: str, data: dict) -> bool:
    """Inserts one dict into the chosen mongodb collection.

    Args:
        collection_name (str)   : Name of the collection to insert data into (e.g. "solar")
        data            (dict)  : The data to insert into the collection

    Returns:
        successful_result (bool)
    """
    client = setup_client()

    database = client[DATABASE_NAME]
    collection = database[collection_name]

    result = collection.insert_one(data)
    successful_result = result.acknowledged

    client.close()

    return successful_result


def mongo_insert_many(collection_name: str, data: list) -> bool:
    """Inserts multiple data points into the chosen mongodb collection.

    Args:
        collection_name (str)   : Name of the collection to insert data into (e.g. "solar")
        data            (list)  : The data to insert into the collection

    Returns:
        successful_result (bool)
    """
    client = setup_client()

    database = client[DATABASE_NAME]
    collection = database[collection_name]

    result = collection.insert_many(data)
    successful_result = result.acknowledged

    client.close()

    return successful_result


def mongo_find_one(collection_name: str, query: dict) -> dict:
    """Finds one record with parameters that match those supplied.

    Args:
        collection_name (str)   : Name of the collection to find data in (e.g. "solar")
        query (dict)  : The query parameters

    Returns:
        result (dict)
    """
    client = setup_client()

    database = client[DATABASE_NAME]
    collection = database[collection_name]

    result = collection.find_one(query)

    client.close()

    return result


def mongo_find(collection_name: str, query: dict) -> list:
    """Finds multiple records with parameters that match those supplied.

    This function returns a list of dicts, each element of the list being a dict
    representing a record in the specified collection that matched the query
    parameters.

    Args:
        collection_name (str)   : Name of the collection to find data in (e.g. "solar")
        query (dict)  : The query parameters

    Returns:
        result (list)
    """
    client = setup_client()

    database = client[DATABASE_NAME]
    collection = database[collection_name]

    result = collection.find(query)
    result = list(result)

    client.close()

    return result
