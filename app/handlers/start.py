"""Handlers for the bot start interaction."""
from __future__ import annotations

from typing import List, Sequence, Tuple

from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.database import MongoCollections
from app.keyboards.main import (
    BACK_BUTTON_KEYBOARD,
    BACK_CALLBACK,
    BRAND_CALLBACK_PREFIX,
    CATALOG_CALLBACK,
    HELP_CALLBACK,
    MAIN_MENU_KEYBOARD,
    build_brands_keyboard,
)

MAIN_MENU_MESSAGE = "Мы рады видеть вас в нашем онлайн помошнике по подбору косметики"
CATALOG_MESSAGE = "Выберите бренд из списка ниже."
HELP_MESSAGE = (
    "наш бот умеееет делать то или другое, и вот для помощи вам телефон нашего администратора"
)

_LAST_BOT_MESSAGE_KEY = "last_bot_message_id"


async def _safe_delete_message(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int
) -> None:
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError:
        pass


async def _cleanup_previous_messages(
    update: Update, context: ContextTypes.DEFAULT_TYPE, *, delete_trigger: bool
) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    stored_id = context.user_data.pop(_LAST_BOT_MESSAGE_KEY, None)
    trigger_message_id = None

    if stored_id is not None:
        await _safe_delete_message(context, chat.id, stored_id)

    if delete_trigger:
        if update.message is not None:
            trigger_message_id = update.message.message_id
        elif update.callback_query is not None and update.callback_query.message:
            trigger_message_id = update.callback_query.message.message_id

        if trigger_message_id is not None and trigger_message_id != stored_id:
            await _safe_delete_message(context, chat.id, trigger_message_id)


def _store_last_message(context: ContextTypes.DEFAULT_TYPE, message: Message) -> None:
    context.user_data[_LAST_BOT_MESSAGE_KEY] = message.message_id


def _get_mongo_collections(context: ContextTypes.DEFAULT_TYPE) -> MongoCollections:
    return context.application.bot_data["mongo"]


async def _send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    await _cleanup_previous_messages(update, context, delete_trigger=True)
    message = await context.bot.send_message(
        chat.id,
        MAIN_MENU_MESSAGE,
        reply_markup=MAIN_MENU_KEYBOARD,
    )
    _store_last_message(context, message)


def _load_brands(context: ContextTypes.DEFAULT_TYPE) -> Sequence[Tuple[int, str]]:
    mongo = _get_mongo_collections(context)
    cursor = mongo.brands.find({}, {"id": 1, "name": 1}).sort("name", 1)
    brands: List[Tuple[int, str]] = []
    for document in cursor:
        try:
            brand_id = int(document.get("id"))
        except (TypeError, ValueError):
            continue
        name = str(document.get("name", "")).strip()
        if not name:
            continue
        brands.append((brand_id, name))
    return brands


async def _show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    await _cleanup_previous_messages(update, context, delete_trigger=False)

    chat = update.effective_chat
    if chat is None:
        return

    brands = _load_brands(context)
    keyboard = build_brands_keyboard(brands)
    message = await context.bot.send_message(
        chat.id,
        CATALOG_MESSAGE,
        reply_markup=keyboard,
    )
    _store_last_message(context, message)


async def _show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    await _cleanup_previous_messages(update, context, delete_trigger=False)

    chat = update.effective_chat
    if chat is None:
        return

    message = await context.bot.send_message(
        chat.id,
        HELP_MESSAGE,
        reply_markup=BACK_BUTTON_KEYBOARD,
    )
    _store_last_message(context, message)


async def _go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is not None:
        await query.answer()
    await _send_main_menu(update, context)


async def _brand_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return

    try:
        brand_id = int(query.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await query.answer("Бренд не найден", show_alert=True)
        return

    mongo = _get_mongo_collections(context)
    brand = mongo.brands.find_one({"id": brand_id}, {"name": 1})
    brand_name = str(brand.get("name")) if brand and brand.get("name") else None
    response = (
        f"Вы выбрали бренд {brand_name}" if brand_name else "Бренд не найден"
    )
    await query.answer(response, show_alert=not bool(brand_name))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command and show the main menu."""

    if update.message is None:
        return
    await _send_main_menu(update, context)


def register_start_handlers(application: Application) -> None:
    """Register handlers responsible for the start command and button."""

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^Старт$"), start))
    application.add_handler(
        CallbackQueryHandler(_show_catalog, pattern=f"^{CATALOG_CALLBACK}$")
    )
    application.add_handler(
        CallbackQueryHandler(_show_help, pattern=f"^{HELP_CALLBACK}$")
    )
    application.add_handler(
        CallbackQueryHandler(_go_back, pattern=f"^{BACK_CALLBACK}$")
    )
    application.add_handler(
        CallbackQueryHandler(
            _brand_selected, pattern=f"^{BRAND_CALLBACK_PREFIX}\\d+$"
        )
    )
