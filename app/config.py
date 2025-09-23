"""Application configuration helpers."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    """Bot configuration loaded from environment variables."""

    bot_token: str
    mongo_uri: str
    mongo_db_name: str
    admin_ids: Tuple[int, ...]
    initial_admin_id: Optional[int]

    @property
    def all_admin_ids(self) -> Tuple[int, ...]:
        """Return a sorted tuple of all known admin ids."""

        ids = set(self.admin_ids)
        if self.initial_admin_id is not None:
            ids.add(self.initial_admin_id)
        return tuple(sorted(ids))


def _parse_admin_ids(raw_value: Optional[str]) -> Tuple[int, ...]:
    """Parse admin identifiers from a comma separated string."""

    if not raw_value:
        return tuple()
    ids = []
    for raw in raw_value.split(","):
        item = raw.strip()
        if not item:
            continue
        try:
            ids.append(int(item))
        except ValueError:
            logger.warning("Unable to parse admin id '%s' from ADMIN_IDS", item)
    return tuple(sorted(set(ids)))


def _parse_initial_admin(raw_value: Optional[str]) -> Optional[int]:
    """Parse the initial admin identifier if provided."""

    if not raw_value:
        return None
    try:
        return int(raw_value)
    except ValueError:
        logger.warning("INITIAL_ADMIN_ID is not a number: %s", raw_value)
        return None


def get_settings() -> Settings:
    """Load settings from the environment and return them."""

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is not configured. Provide it via environment variables."
        )
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError(
            "MONGO_URI is not configured. Provide it via environment variables."
        )
    mongo_db_name = os.getenv("MONGO_DB_NAME", "tg_cosmetics")
    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS"))
    initial_admin_id = _parse_initial_admin(os.getenv("INITIAL_ADMIN_ID"))

    return Settings(
        bot_token=token,
        mongo_uri=mongo_uri,
        mongo_db_name=mongo_db_name,
        admin_ids=admin_ids,
        initial_admin_id=initial_admin_id,
    )
