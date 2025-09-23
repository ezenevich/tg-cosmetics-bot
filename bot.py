"""Entry point for the festive Telegram bot."""
from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder

from app.config import get_settings
from app.database import create_mongo_collections
from app.handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the Telegram bot."""

    settings = get_settings()
    application = ApplicationBuilder().token(settings.bot_token).build()

    mongo_collections = create_mongo_collections(settings)
    application.bot_data["mongo"] = mongo_collections
    application.bot_data["settings"] = settings

    register_handlers(application)

    logger.info("Bot started. Waiting for updates…")
    application.run_polling()


if __name__ == "__main__":
    main()
