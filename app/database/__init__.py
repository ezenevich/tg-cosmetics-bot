"""MongoDB helpers and connection utilities."""
from __future__ import annotations

from dataclasses import dataclass

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import Settings

__all__ = ["MongoCollections", "create_mongo_collections"]


@dataclass
class MongoCollections:
    """Container for frequently used MongoDB collections."""

    client: MongoClient
    database: Database
    admins: Collection
    brands: Collection
    categories: Collection
    products: Collection


def create_mongo_collections(settings: Settings) -> MongoCollections:
    """Create a Mongo client and return commonly used collections."""

    client = MongoClient(settings.mongo_uri)
    database = client[settings.mongo_db_name]
    return MongoCollections(
        client=client,
        database=database,
        admins=database["admins"],
        brands=database["brands"],
        categories=database["categories"],
        products=database["products"],
    )
