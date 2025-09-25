"""Handlers for the bot start interaction."""
from __future__ import annotations

import base64
import binascii
import html
import io
from typing import List, Sequence, Tuple

from telegram import InputFile, Message, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from telegram.constants import ParseMode

from app.database import MongoCollections
from app.keyboards.main import (
    BACK_BUTTON_KEYBOARD,
    BACK_CALLBACK,
    BRAND_CALLBACK_PREFIX,
    CATALOG_CALLBACK,
    CATEGORY_BACK_CALLBACK_PREFIX,
    CATEGORY_CALLBACK_PREFIX,
    HELP_CALLBACK,
    MAIN_MENU_KEYBOARD,
    build_brands_keyboard,
    build_categories_keyboard,
    build_product_details_keyboard,
    build_products_keyboard,
    PRODUCT_CALLBACK_PREFIX,
)

MAIN_MENU_MESSAGE = "Мы рады видеть вас в нашем онлайн помошнике по подбору косметики"
CATALOG_MESSAGE = "Выберите бренд из списка ниже:"
HELP_MESSAGE = (
    "наш бот умеет делать то или другое, и вот для помощи вам телефон нашего администратора"
)
CATEGORIES_MESSAGE_TEMPLATE = "Выберите категорию бренда {brand}:"
PRODUCTS_MESSAGE_TEMPLATE = "Выберите продукт категории {category} бренда {brand}:"
PRODUCTS_EMPTY_MESSAGE_TEMPLATE = (
    "Для категории {category} бренда {brand} пока нет продуктов."
)

_LAST_BOT_MESSAGE_KEY = "last_bot_message_id"
_LAST_BOT_MESSAGE_TYPE_KEY = "last_bot_message_type"


async def _safe_delete_message(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int
) -> None:
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError:
        pass


def _is_start_trigger_message(message: Message | None) -> bool:
    """Return ``True`` if the message contains the start command or button text."""

    if message is None:
        return False

    text = message.text or message.caption or ""
    normalized = text.strip().casefold()

    if not normalized:
        return False

    return normalized.startswith("/start") or normalized == "старт"


async def _cleanup_previous_messages(
    update: Update, context: ContextTypes.DEFAULT_TYPE, *, delete_trigger: bool
) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    stored_id = context.user_data.pop(_LAST_BOT_MESSAGE_KEY, None)
    if stored_id is not None:
        context.user_data.pop(_LAST_BOT_MESSAGE_TYPE_KEY, None)
    trigger_message_id = None

    if stored_id is not None:
        await _safe_delete_message(context, chat.id, stored_id)

    trigger_message: Message | None = None

    if delete_trigger:
        if update.message is not None:
            trigger_message = update.message
        elif update.callback_query is not None and update.callback_query.message:
            trigger_message = update.callback_query.message

        if trigger_message is not None:
            trigger_message_id = trigger_message.message_id

        if (
            trigger_message_id is not None
            and trigger_message_id != stored_id
            and not _is_start_trigger_message(trigger_message)
        ):
            await _safe_delete_message(context, chat.id, trigger_message_id)


def _store_last_message(
    context: ContextTypes.DEFAULT_TYPE, message: Message, *, message_type: str
) -> None:
    context.user_data[_LAST_BOT_MESSAGE_KEY] = message.message_id
    context.user_data[_LAST_BOT_MESSAGE_TYPE_KEY] = message_type


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
    _store_last_message(context, message, message_type="main_menu")


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


def _load_categories(context: ContextTypes.DEFAULT_TYPE) -> Sequence[Tuple[int, str]]:
    mongo = _get_mongo_collections(context)
    cursor = mongo.categories.find({}, {"id": 1, "name": 1}).sort("name", 1)
    categories: List[Tuple[int, str]] = []
    for document in cursor:
        try:
            category_id = int(document.get("id"))
        except (TypeError, ValueError):
            continue
        name = str(document.get("name", "")).strip()
        if not name:
            continue
        categories.append((category_id, name))

    # Переносим категорию «прочее» в конец списка независимо от алфавитного порядка
    categories.sort(
        key=lambda item: (item[1].strip().lower() == "прочее", item[1].strip().lower())
    )
    return categories


def _load_products(
    context: ContextTypes.DEFAULT_TYPE, *, brand_id: int, category_id: int
) -> Sequence[Tuple[int, str]]:
    mongo = _get_mongo_collections(context)
    cursor = mongo.products.find(
        {"brand_id": brand_id, "category_id": category_id},
        {"id": 1, "name": 1},
    ).sort("name", 1)
    products: List[Tuple[int, str]] = []
    for document in cursor:
        try:
            product_id = int(document.get("id"))
        except (TypeError, ValueError):
            continue
        name = str(document.get("name", "")).strip()
        if not name:
            continue
        products.append((product_id, name))
    return products


async def _send_categories_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    brand_id: int,
    brand_name: str,
    categories: Sequence[Tuple[int, str]],
) -> None:
    await _cleanup_previous_messages(update, context, delete_trigger=False)

    chat = update.effective_chat
    if chat is None:
        return

    keyboard = build_categories_keyboard(categories, brand_id=brand_id)
    message = await context.bot.send_message(
        chat.id,
        CATEGORIES_MESSAGE_TEMPLATE.format(brand=brand_name),
        reply_markup=keyboard,
    )
    _store_last_message(context, message, message_type=f"categories:{brand_id}")


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
    _store_last_message(context, message, message_type="catalog")


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
    _store_last_message(context, message, message_type="help")


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
    if not brand_name:
        await query.answer("Бренд не найден", show_alert=True)
        return

    categories = _load_categories(context)
    if not categories:
        await query.answer("Категории не найдены", show_alert=True)
        return

    await query.answer()
    await _send_categories_menu(
        update,
        context,
        brand_id=brand_id,
        brand_name=brand_name,
        categories=categories,
    )


async def _category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return

    data = query.data.split(":", 1)[1]
    try:
        brand_part, category_part = data.split(":", 1)
        brand_id = int(brand_part)
        category_id = int(category_part)
    except (ValueError, IndexError):
        await query.answer("Категория не найдена", show_alert=True)
        return

    mongo = _get_mongo_collections(context)
    brand = mongo.brands.find_one({"id": brand_id}, {"name": 1})
    category = mongo.categories.find_one({"id": category_id}, {"name": 1})

    brand_name = str(brand.get("name")) if brand and brand.get("name") else None
    category_name = (
        str(category.get("name")) if category and category.get("name") else None
    )

    if not brand_name or not category_name:
        await query.answer("Категория не найдена", show_alert=True)
        return

    products = _load_products(context, brand_id=brand_id, category_id=category_id)

    await query.answer()

    chat = update.effective_chat
    if chat is None:
        return

    await _cleanup_previous_messages(update, context, delete_trigger=False)

    keyboard = build_products_keyboard(
        products, brand_id=brand_id, category_id=category_id
    )

    if products:
        text = PRODUCTS_MESSAGE_TEMPLATE.format(
            brand=brand_name, category=category_name
        )
    else:
        text = PRODUCTS_EMPTY_MESSAGE_TEMPLATE.format(
            brand=brand_name, category=category_name
        )

    message = await context.bot.send_message(
        chat.id,
        text,
        reply_markup=keyboard,
    )
    _store_last_message(
        context,
        message,
        message_type=f"products:{brand_id}:{category_id}",
    )


async def _categories_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    if not brand_name:
        await query.answer("Бренд не найден", show_alert=True)
        return

    categories = _load_categories(context)
    if not categories:
        await query.answer("Категории не найдены", show_alert=True)
        return

    await query.answer()
    await _send_categories_menu(
        update,
        context,
        brand_id=brand_id,
        brand_name=brand_name,
        categories=categories,
    )


async def _product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return

    try:
        data = query.data.split(":", 1)[1]
        brand_part, category_part, product_part = data.split(":", 2)
        brand_id = int(brand_part)
        category_id = int(category_part)
        product_id = int(product_part)
    except (IndexError, ValueError):
        await query.answer("Продукт не найден", show_alert=True)
        return

    mongo = _get_mongo_collections(context)
    product = mongo.products.find_one(
        {"id": product_id},
        {
            "name": 1,
            "code": 1,
            "description": 1,
            "link": 1,
            "image_base64": 1,
            "brand_id": 1,
            "category_id": 1,
        },
    )

    if (
        not product
        or int(product.get("brand_id", -1)) != brand_id
        or int(product.get("category_id", -1)) != category_id
    ):
        await query.answer("Продукт не найден", show_alert=True)
        return

    await query.answer()

    chat = update.effective_chat
    if chat is None:
        return

    await _cleanup_previous_messages(update, context, delete_trigger=False)

    name = html.escape(str(product.get("name", "")).strip())
    code = html.escape(str(product.get("code", "")).strip())
    description_raw = str(product.get("description", "")).strip()
    description = html.escape(description_raw).replace("\n", "<br>")
    link = str(product.get("link", "")).strip()

    caption_parts: list[str] = []
    if name:
        caption_parts.append(f"<b>{name}</b>")
    if code:
        caption_parts.extend(["", f"<i>Артикул: {code}</i>"])
    if description:
        caption_parts.extend(["", f"<blockquote>{description}</blockquote>"])
    if link:
        caption_parts.extend(
            ["", f'<a href="{html.escape(link, quote=True)}">подробнее о продукте</a>']
        )

    caption = "\n".join(caption_parts) if caption_parts else ""

    image_base64 = str(product.get("image_base64", "")).strip()
    message: Message | None = None

    if image_base64:
        try:
            photo_bytes = base64.b64decode(image_base64)
        except (binascii.Error, ValueError):
            photo_bytes = b""
        if photo_bytes:
            photo_io = io.BytesIO(photo_bytes)
            photo_io.name = f"product_{product_id}.jpg"
            message = await context.bot.send_photo(
                chat.id,
                photo=InputFile(photo_io),
                caption=caption or None,
                parse_mode=ParseMode.HTML,
                reply_markup=build_product_details_keyboard(
                    brand_id=brand_id, category_id=category_id
                ),
            )

    if message is None:
        message = await context.bot.send_message(
            chat.id,
            caption or "Информация о продукте недоступна",
            parse_mode=ParseMode.HTML,
            reply_markup=build_product_details_keyboard(
                brand_id=brand_id, category_id=category_id
            ),
        )

    _store_last_message(
        context,
        message,
        message_type=f"product_details:{brand_id}:{category_id}:{product_id}",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command and show the main menu."""

    message = update.message
    chat = update.effective_chat
    if message is None or chat is None:
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
    application.add_handler(
        CallbackQueryHandler(
            _category_selected,
            pattern=f"^{CATEGORY_CALLBACK_PREFIX}\\d+:\\d+$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            _categories_back,
            pattern=f"^{CATEGORY_BACK_CALLBACK_PREFIX}\\d+$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            _product_selected,
            pattern=f"^{PRODUCT_CALLBACK_PREFIX}\\d+:\\d+:\\d+$",
        )
    )
