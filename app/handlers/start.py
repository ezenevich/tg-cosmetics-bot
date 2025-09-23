"""Handlers for /start command."""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Send a thank-you message to the user."""

    await message.answer(
        "Спасибо, что написали! Мы уже получили ваше сообщение и свяжемся с вами в ближайшее время."
    )
