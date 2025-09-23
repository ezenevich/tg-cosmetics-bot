"""Definitions of reply keyboards used by the bot."""
from telegram import ReplyKeyboardMarkup

START_KEYBOARD = ReplyKeyboardMarkup(
    [["Старт"]],
    resize_keyboard=True,
)
