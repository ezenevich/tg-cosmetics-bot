"""Telegram game bot entry point."""
from __future__ import annotations

import logging
import os
from typing import Iterable, List, Optional, Set

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from telegram import ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

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

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured. Provide it via environment variables.")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not configured. Provide it via environment variables.")

ADMIN_IDS: Set[int] = set()
if ADMIN_IDS_ENV:
    for raw_id in ADMIN_IDS_ENV.split(","):
        raw_id = raw_id.strip()
        if raw_id:
            try:
                ADMIN_IDS.add(int(raw_id))
            except ValueError:
                logger.warning("Unable to parse admin id '%s' from ADMIN_IDS", raw_id)
if INITIAL_ADMIN_ID:
    try:
        ADMIN_IDS.add(int(INITIAL_ADMIN_ID))
    except ValueError:  # pragma: no cover - defensive
        logger.warning("INITIAL_ADMIN_ID is not a number: %s", INITIAL_ADMIN_ID)

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB_NAME]
users: Collection = db["users"]
buttons: Collection = db["buttons"]
game_collection: Collection = db["game"]

PLAYER_LIMIT = 9

START_KEYBOARD = ReplyKeyboardMarkup(
    [["Обновить меню"], ["/start"]],
    resize_keyboard=True,
)


def get_game() -> dict:
    game = game_collection.find_one({})
    if game:
        return game
    game_template = {
        "status": "setup",
        "admin_ids": sorted(ADMIN_IDS),
    }
    game_collection.insert_one(game_template)
    return game_collection.find_one({})


def is_admin(game: dict, tg_id: int) -> bool:
    admin_ids = set(game.get("admin_ids", [])) | ADMIN_IDS
    return tg_id in admin_ids


async def send_menu(
    chat_id: int,
    user: dict,
    game: dict,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    status = game.get("status", "setup")
    role = "Администратор" if user.get("isAdmin") else "Игрок"
    number = user.get("number")
    pieces: List[str] = [
        f"Статус игры: <b>{status}</b>",
        f"Роль: <b>{role}</b>",
    ]
    if number:
        pieces.append(
            f"Ваши фигуры: {number_to_square(number)} {number_to_circle(number)}"
        )
    if user.get("discovered_opponent_ids"):
        pieces.append(
            "Обнаруженные оппоненты: "
            + ", ".join(map(str, user["discovered_opponent_ids"]))
        )
    if status != "running" and user.get("isAdmin"):
        pieces.append("Запустите игру командой /game_start")
    await context.bot.send_message(
        chat_id,
        "\n".join(pieces),
        reply_markup=START_KEYBOARD,
        parse_mode=ParseMode.HTML,
    )


def number_to_square(number: Optional[int]) -> str:
    if not number:
        return "⬜"
    return f"⬛{number}"


def number_to_circle(number: Optional[int]) -> str:
    if not number:
        return "⚪"
    return f"⚫{number}"


def get_name(user: dict) -> str:
    components: Iterable[str] = filter(
        None,
        [user.get("first_name"), user.get("last_name"), user.get("username")],
    )
    return " ".join(components) or str(user.get("telegram_id"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_id = update.effective_user.id
    game = get_game()
    user = users.find_one({"telegram_id": tg_id})
    if not user:
        if game.get("status") == "running" and not is_admin(game, tg_id):
            await update.message.reply_text(
                "Игра уже идет, присоединиться нельзя.",
                reply_markup=START_KEYBOARD,
            )
            return
        is_admin_flag = is_admin(game, tg_id)
        number = None
        if not is_admin_flag:
            player_count = users.count_documents({"isAdmin": {"$ne": True}})
            if player_count >= PLAYER_LIMIT:
                await update.message.reply_text(
                    "Нужное количество игроков уже в игре.",
                    reply_markup=START_KEYBOARD,
                )
                return
            number = player_count + 1
        users.insert_one(
            {
                "telegram_id": tg_id,
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
                "last_name": update.effective_user.last_name,
                "alive": True,
                "discovered_opponent_ids": [],
                "special_button_ids": [],
                "isAdmin": is_admin_flag,
                "number": number,
            }
        )
        user = users.find_one({"telegram_id": tg_id})
        if not is_admin_flag and number:
            buttons.update_one(
                {"number": number, "special": False},
                {
                    "$set": {
                        "taken": True,
                        "blocked": False,
                        "player_id": user["_id"],
                        "code_used": False,
                    }
                },
                upsert=True,
            )
            for admin_id in game.get("admin_ids", []):
                await context.bot.send_message(
                    admin_id,
                    f"Подключился игрок {get_name(user)} {number_to_square(number)}{number_to_circle(number)}",
                )
    if not user.get("alive", True):
        await update.message.reply_text(
            "Вас заблокировали 🚫. Игра окончена.", reply_markup=START_KEYBOARD
        )
        return
    if game.get("status") != "running":
        if is_admin(game, tg_id):
            await send_menu(tg_id, user, game, context)
        else:
            await update.message.reply_text(
                "Игра еще не началась.", reply_markup=START_KEYBOARD
            )
        return
    await send_menu(tg_id, user, game, context)


async def game_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = get_game()
    tg_id = update.effective_user.id
    if not is_admin(game, tg_id):
        await update.message.reply_text("Команда доступна только администраторам.")
        return
    game_collection.update_one({}, {"$set": {"status": "running"}}, upsert=True)
    await update.message.reply_text("Игра запущена! Игроки могут присоединяться.")


async def game_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = get_game()
    tg_id = update.effective_user.id
    if not is_admin(game, tg_id):
        await update.message.reply_text("Команда доступна только администраторам.")
        return
    game_collection.update_one({}, {"$set": {"status": "finished"}}, upsert=True)
    await update.message.reply_text("Игра остановлена.")


async def game_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = get_game()
    tg_id = update.effective_user.id
    if not is_admin(game, tg_id):
        await update.message.reply_text("Команда доступна только администраторам.")
        return
    users.delete_many({"isAdmin": {"$ne": True}})
    buttons.update_many({}, {"$set": {"taken": False, "player_id": None, "code_used": False}})
    game_collection.update_one({}, {"$set": {"status": "setup"}}, upsert=True)
    await update.message.reply_text("Игра и данные игроков сброшены.")


def register_admin_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("game_start", game_start))
    application.add_handler(CommandHandler("game_stop", game_stop))
    application.add_handler(CommandHandler("game_reset", game_reset))


def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    register_admin_handlers(application)

    logger.info("Bot started. Waiting for updates…")
    application.run_polling()


if __name__ == "__main__":
    main()
