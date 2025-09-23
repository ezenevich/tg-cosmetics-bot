"""Utility script to initialise MongoDB collections for the bot."""
from __future__ import annotations

import argparse
import logging
import os
from typing import Iterable, List

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "tg_cosmetics")
INITIAL_ADMIN_ID = os.getenv("INITIAL_ADMIN_ID")
ADMIN_IDS_ENV = os.getenv("ADMIN_IDS")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not configured. Provide it via environment variables.")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
users = db["users"]
buttons = db["buttons"]
game_collection = db["game"]


def parse_admin_ids() -> List[int]:
    ids: List[int] = []
    env_values: Iterable[str] = []
    if ADMIN_IDS_ENV:
        env_values = [value.strip() for value in ADMIN_IDS_ENV.split(",") if value.strip()]
    if INITIAL_ADMIN_ID:
        env_values = list(env_values) + [INITIAL_ADMIN_ID]
    for raw in env_values:
        try:
            ids.append(int(raw))
        except ValueError:
            logger.warning("Unable to parse admin id '%s'", raw)
    return ids


def ensure_game_document() -> None:
    existing = game_collection.find_one({})
    if existing:
        logger.info("Game document already exists with status '%s'", existing.get("status"))
        update = {}
        admin_ids = sorted(set(existing.get("admin_ids", [])) | set(parse_admin_ids()))
        if admin_ids != existing.get("admin_ids", []):
            update["admin_ids"] = admin_ids
        if update:
            game_collection.update_one({"_id": existing["_id"]}, {"$set": update})
        return
    game_collection.insert_one({
        "status": "setup",
        "admin_ids": parse_admin_ids(),
    })
    logger.info("Created default game document")


def ensure_buttons_collection(reset: bool) -> None:
    if reset:
        buttons.delete_many({})
        logger.info("Buttons collection cleared")
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
        logger.info("Inserted %s default buttons", len(new_docs))
    else:
        logger.info("Buttons already initialised")


def reset_players() -> None:
    deleted = users.delete_many({"isAdmin": {"$ne": True}})
    if deleted.deleted_count:
        logger.info("Removed %s player profiles", deleted.deleted_count)
    else:
        logger.info("No non-admin players to remove")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise MongoDB for the Telegram bot")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop non-admin players and re-create buttons before starting the game",
    )
    args = parser.parse_args()

    ensure_game_document()
    ensure_buttons_collection(reset=args.reset)
    if args.reset:
        reset_players()

    logger.info("Initialisation complete")


if __name__ == "__main__":
    main()
