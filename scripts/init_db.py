"""Utility script to initialise MongoDB collections for the bot."""
from __future__ import annotations

import argparse
import logging

from app.config import get_settings
from app.database import create_mongo_collections
from app.database.management import (
    ensure_buttons_collection,
    ensure_game_document,
    reset_players,
)


def main() -> None:
    """Initialise MongoDB collections required by the bot."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Initialise MongoDB collections for the Telegram bot",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Очистить игроков и кнопки перед новой игрой",
    )
    args = parser.parse_args()

    settings = get_settings()
    collections = create_mongo_collections(settings)

    ensure_game_document(collections, settings.all_admin_ids)
    ensure_buttons_collection(collections.buttons, reset=args.reset)
    if args.reset:
        reset_players(collections.users)

    logging.getLogger(__name__).info("Инициализация базы данных завершена")

    collections.client.close()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
