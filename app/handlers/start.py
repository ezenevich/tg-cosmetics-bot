"""Handlers for the bot start interaction."""
from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.keyboards.main import START_KEYBOARD

CONGRATULATIONS_MESSAGE = "Поздравляю с праздником! 🎉"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a festive greeting to the user."""

    if update.message is None:
        return
    await update.message.reply_text(CONGRATULATIONS_MESSAGE, reply_markup=START_KEYBOARD)


def register_start_handlers(application: Application) -> None:
    """Register handlers responsible for the start command and button."""

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^Старт$"), start))
