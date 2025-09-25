"""Utility script to initialise MongoDB collections for the bot."""
from __future__ import annotations

import logging

from app.config import get_settings
from app.database import create_mongo_collections
from app.database.management import (
    DEFAULT_BRANDS,
    ensure_admins_collection,
    ensure_brands_collection,
)


def main() -> None:
    """Initialise MongoDB collections required by the bot."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = get_settings()
    collections = create_mongo_collections(settings)

    ensure_brands_collection(collections.brands, DEFAULT_BRANDS)
    ensure_admins_collection(collections.admins, settings.initial_admin_id)

    logging.getLogger(__name__).info("Инициализация базы данных завершена")

    collections.client.close()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
