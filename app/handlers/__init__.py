"""Helpers for registering bot handlers."""
from telegram.ext import Application

from app.handlers.start import register_start_handlers

__all__ = ["register_handlers"]


def register_handlers(application: Application) -> None:
    """Register all handlers used by the bot."""

    register_start_handlers(application)
