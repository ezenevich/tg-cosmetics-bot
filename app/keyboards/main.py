"""Definitions of inline keyboards used by the bot."""
from __future__ import annotations

from typing import Sequence, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CATALOG_CALLBACK = "main:catalog"
HELP_CALLBACK = "main:help"
BACK_CALLBACK = "main:back"
BRAND_CALLBACK_PREFIX = "brand:"

MAIN_MENU_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("📋 КАТАЛОГ", callback_data=CATALOG_CALLBACK),
            InlineKeyboardButton("🆘 ПОМОЩЬ", callback_data=HELP_CALLBACK),
        ]
    ]
)

BACK_BUTTON_KEYBOARD = InlineKeyboardMarkup(
    [[InlineKeyboardButton("⬅️ НАЗАД", callback_data=BACK_CALLBACK)]]
)


def build_brands_keyboard(brands: Sequence[Tuple[int, str]]) -> InlineKeyboardMarkup:
    """Return an inline keyboard with a button for every provided brand."""

    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                name, callback_data=f"{BRAND_CALLBACK_PREFIX}{brand_id}"
            )
        ]
        for brand_id, name in brands
    ]
    rows.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data=BACK_CALLBACK)])
    return InlineKeyboardMarkup(rows)
