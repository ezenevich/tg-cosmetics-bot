"""Utility helpers for preparing MongoDB collections."""
from __future__ import annotations

import logging
from typing import Sequence

from pymongo.collection import Collection

from app.database import MongoCollections

__all__ = [
    "ensure_game_document",
    "ensure_buttons_collection",
    "ensure_brands_collection",
    "reset_players",
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


def ensure_game_document(collections: MongoCollections, admin_ids: Sequence[int]) -> None:
    """Create a default game document or update admin ids if needed."""

    desired_admins = set(admin_ids)
    existing = collections.game.find_one({})
    if existing:
        update = {}
        current_admins = set(existing.get("admin_ids", []))
        combined = sorted(current_admins | desired_admins)
        if combined != existing.get("admin_ids", []):
            update["admin_ids"] = combined
        if update:
            collections.game.update_one({"_id": existing["_id"]}, {"$set": update})
            logger.info("Обновлены администраторы в документе игры")
        else:
            logger.info(
                "Документ игры уже существует со статусом '%s'",
                existing.get("status"),
            )
        return

    collections.game.insert_one({
        "status": "setup",
        "admin_ids": sorted(desired_admins),
    })
    logger.info("Создан документ игры по умолчанию")


def ensure_buttons_collection(buttons: Collection, *, reset: bool) -> None:
    """Populate the buttons collection with default entries."""

    if reset:
        deleted = buttons.delete_many({})
        if deleted.deleted_count:
            logger.info("Коллекция кнопок очищена")
        else:
            logger.info("Коллекция кнопок уже пуста")

    existing_numbers = {
        doc["number"] for doc in buttons.find({"special": False}, {"number": 1})
    }
    new_docs = []
    for number in range(1, 10):
        if number in existing_numbers:
            continue
        new_docs.append(
            {
                "number": number,
                "special": False,
                "taken": False,
                "blocked": False,
                "player_id": None,
                "code_used": False,
            }
        )
    if new_docs:
        buttons.insert_many(new_docs)
        logger.info("Добавлено %s стандартных кнопок", len(new_docs))
    else:
        logger.info("Кнопки уже инициализированы")


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


def reset_players(users: Collection) -> None:
    """Remove all non-admin players from the users collection."""

    deleted = users.delete_many({"isAdmin": {"$ne": True}})
    if deleted.deleted_count:
        logger.info("Удалено %s профилей игроков", deleted.deleted_count)
    else:
        logger.info("Нет игроков для удаления")
