"""Helpers for working with product documents in MongoDB."""
from __future__ import annotations

from typing import Mapping, MutableMapping

from pymongo.collection import Collection

from app.database.models import Product

__all__ = ["create_product", "prepare_product_document"]


def _next_incremental_id(collection: Collection) -> int:
    """Return the next identifier for the provided collection."""

    last_document = collection.find_one(sort=[("id", -1)], projection={"id": 1})
    if not last_document:
        return 1
    return int(last_document.get("id", 0)) + 1


def prepare_product_document(data: Mapping[str, object], *, collection: Collection) -> MutableMapping[str, object]:
    """Prepare a MongoDB document for insertion ensuring an incremental id."""

    new_id = _next_incremental_id(collection)
    document = dict(data)
    document["id"] = new_id
    return document


def create_product(collection: Collection, data: Mapping[str, object]) -> Product:
    """Insert a new product into MongoDB with an incremental identifier."""

    document = prepare_product_document(data, collection=collection)
    collection.insert_one(document)
    return Product(**document)  # type: ignore[arg-type]
