"""Dataclasses describing MongoDB entities used by the bot."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

__all__ = ["Brand", "Category", "Product"]


@dataclass(frozen=True)
class Brand:
    """Representation of a cosmetic brand stored in MongoDB."""

    id: int
    name: str

    def to_document(self) -> Dict[str, Any]:
        """Return a MongoDB document representation of the brand."""

        return asdict(self)


@dataclass(frozen=True)
class Category:
    """Representation of a product category stored in MongoDB."""

    id: int
    name: str

    def to_document(self) -> Dict[str, Any]:
        """Return a MongoDB document representation of the category."""

        return asdict(self)


@dataclass(frozen=True)
class Product:
    """Representation of a cosmetic product stored in MongoDB."""

    id: int
    photo: str
    name: str
    code: str
    description: str
    link: str
    brand: int
    category: str

    def to_document(self) -> Dict[str, Any]:
        """Return a MongoDB document representation of the product."""

        return asdict(self)
