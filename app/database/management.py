"""Utility helpers for preparing MongoDB collections."""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Optional, Sequence

from pymongo.collection import Collection

from app.database import MongoCollections

__all__ = [
    "ensure_brands_collection",
    "ensure_admins_collection",
    "ensure_categories_collection",
    "load_products_from_file",
    "DEFAULT_BRANDS",
    "DEFAULT_CATEGORIES",
    "DEFAULT_PRODUCTS_FILE",
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


DEFAULT_CATEGORIES = (
    "шампунь",
    "кондиционер",
    "маска",
    "лосьон",
    "сыворотка",
    "прочее",
)


DEFAULT_PRODUCTS_FILE = Path(__file__).with_name("default_products.json")

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


def ensure_categories_collection(
    categories: Collection, category_names: Sequence[str]
) -> None:
    """Populate the categories collection with default category names."""

    existing = {
        doc["name"]: int(doc.get("id", 0))
        for doc in categories.find({}, {"name": 1, "id": 1})
    }
    next_id = (max(existing.values()) if existing else 0) + 1
    new_docs = []
    for name in category_names:
        if name in existing:
            continue
        new_docs.append({"id": next_id, "name": name})
        next_id += 1
    if new_docs:
        categories.insert_many(new_docs)
        logger.info("Добавлено %s категорий", len(new_docs))
    else:
        logger.info("Коллекция категорий уже инициализирована")


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


def load_products_from_file(
    products: Collection,
    brands: Collection,
    categories: Collection,
    file_path: Path | str,
) -> None:
    """Load initial products from a JSON file into the products collection."""

    path = Path(file_path)
    if not path.exists():
        logger.warning("Файл с продуктами %s не найден", path)
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Не удалось загрузить стартовые продукты: %s", exc)
        return

    if not isinstance(data, list):
        logger.error("Формат файла с продуктами некорректен: ожидался список")
        return

    brand_map = {
        str(doc.get("name", "")).strip().lower(): int(doc.get("id", 0))
        for doc in brands.find({}, {"name": 1, "id": 1})
    }
    category_map = {
        str(doc.get("name", "")).strip().lower(): int(doc.get("id", 0))
        for doc in categories.find({}, {"name": 1, "id": 1})
    }

    existing_codes = {
        str(doc.get("code", "")).strip().lower()
        for doc in products.find({}, {"code": 1})
    }
    last_product = products.find_one(sort=[("id", -1)], projection={"id": 1})
    next_id = int(last_product.get("id", 0)) + 1 if last_product else 1

    new_documents = []
    for raw in data:
        if not isinstance(raw, dict):
            continue

        code = str(raw.get("code", "")).strip()
        name = str(raw.get("name", "")).strip()
        description = str(raw.get("description", "")).strip()
        link = str(raw.get("link", "")).strip()
        image_base64 = str(raw.get("image_base64", "")).strip()
        image_path_value = raw.get("image_path")
        if not image_base64 and image_path_value:
            image_path = Path(str(image_path_value))
            if not image_path.is_absolute():
                if image_path.exists():
                    image_path = image_path.resolve()
                else:
                    image_path = (path.parent / image_path).resolve()
            try:
                image_base64 = base64.b64encode(image_path.read_bytes()).decode()
            except OSError as exc:
                logger.warning(
                    "Не удалось прочитать изображение для продукта %s: %s", code or name, exc
                )
                image_base64 = ""
        brand_name = str(raw.get("brand", "")).strip().lower()
        category_name = str(raw.get("category", "")).strip().lower()

        if not code or code.lower() in existing_codes:
            continue
        if not name:
            logger.warning("Пропущен продукт без названия с кодом %s", code)
            continue

        brand_id = brand_map.get(brand_name)
        if brand_id is None:
            logger.warning(
                "Для продукта %s не найдена запись бренда '%s'", code, brand_name
            )
            continue

        category_id = category_map.get(category_name)
        if category_id is None:
            logger.warning(
                "Для продукта %s не найдена запись категории '%s'", code, category_name
            )
            continue

        if not image_base64:
            logger.warning("Для продукта %s не удалось получить изображение", code)

        document = {
            "id": next_id,
            "code": code,
            "name": name,
            "description": description,
            "link": link,
            "image_base64": image_base64,
            "brand_id": brand_id,
            "category_id": category_id,
        }

        new_documents.append(document)
        existing_codes.add(code.lower())
        next_id += 1

    if not new_documents:
        logger.info("Новые продукты для добавления отсутствуют")
        return

    products.insert_many(new_documents)
    logger.info("Добавлено %s продуктов", len(new_documents))
