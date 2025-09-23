"""Application routers."""
from aiogram import Dispatcher

from . import start


def register_handlers(dp: Dispatcher) -> None:
    """Register all application routers."""

    dp.include_router(start.router)
