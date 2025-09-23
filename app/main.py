"""Application entry point."""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any, Awaitable, Callable

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from .config import get_settings
from .db.mongodb import MongoDB
from .handlers import register_handlers


def _setup_logging() -> None:
    """Configure basic logging for the application."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )


def _create_startup_hook(mongo: MongoDB, admin_id: int) -> Callable[..., Awaitable[None]]:
    async def on_startup(*_: Any) -> None:
        await mongo.ensure_admin(admin_id)

    return on_startup


def _create_shutdown_hook(mongo: MongoDB) -> Callable[..., Awaitable[None]]:
    async def on_shutdown(*_: Any) -> None:
        mongo.close()

    return on_shutdown


async def main() -> None:
    """Run the bot."""

    if sys.platform != "win32":
        import uvloop

        uvloop.install()

    _setup_logging()

    settings = get_settings()
    mongo = MongoDB(settings.mongo_uri, settings.mongo_db)

    bot = Bot(token=settings.bot_token.get_secret_value(), parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dp.startup.register(_create_startup_hook(mongo, settings.initial_admin_id))
    dp.shutdown.register(_create_shutdown_hook(mongo))

    register_handlers(dp)

    try:
        await dp.start_polling(bot)
    finally:
        mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
