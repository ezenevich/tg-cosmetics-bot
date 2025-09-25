"""Utility helpers for preparing MongoDB collections."""
from __future__ import annotations

import logging
from typing import Optional, Sequence

from pymongo.collection import Collection

from app.database import MongoCollections

__all__ = [
    "ensure_brands_collection",
    "ensure_admins_collection",
    "DEFAULT_BRANDS",
]

logger = logging.getLogger(__name__)


DEFAULT_BRANDS = (
    "ARTFOLIO",
    "KAARAL",
    "INEBRYA",
    "HELEN SEWARD",
    "FARCOM",
    "KAYPRO",
    "FANOLA",
    "JEM",
    "OCEANYST",
)

def ensure_brands_collection(brands: Collection, brand_names: Sequence[str]) -> None:
    """Populate the brands collection with default brand names."""

    existing = {
        doc["name"]: int(doc.get("id", 0))
        for doc in brands.find({}, {"name": 1, "id": 1})
    }
    next_id = (max(existing.values()) if existing else 0) + 1
    new_docs = []
    for name in brand_names:
        if name in existing:
            continue
        new_docs.append({"id": next_id, "name": name})
        next_id += 1
    if new_docs:
        brands.insert_many(new_docs)
        logger.info("Добавлено %s брендов", len(new_docs))
    else:
        logger.info("Коллекция брендов уже инициализирована")


def ensure_admins_collection(
    admins: Collection, initial_admin_id: Optional[int]
) -> None:
    """Ensure the initial administrator exists in the admins collection."""

    if initial_admin_id is None:
        logger.info("INITIAL_ADMIN_ID не задан, коллекция администраторов не изменена")
        return

    existing = admins.find_one(
        {"telegram_id": initial_admin_id},
        projection={"id": 1},
    )
    if existing:
        logger.info(
            "Администратор с telegram_id=%s уже существует", initial_admin_id
        )
        return

    last = admins.find_one(sort=[("id", -1)], projection={"id": 1})
    next_id = int(last.get("id", 0)) + 1 if last else 1

    admins.insert_one({"id": next_id, "telegram_id": initial_admin_id})
    logger.info(
        "Добавлен администратор с id=%s и telegram_id=%s", next_id, initial_admin_id
    )
