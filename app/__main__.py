"""Executable module for running the bot with ``python -m app``."""
import asyncio

from .main import main

if __name__ == "__main__":
    asyncio.run(main())
