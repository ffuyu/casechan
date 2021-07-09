from typing import Optional, Union

from pydantic import root_validator

from .engine import engine
from .models import ModelPlus

__all__ = (
    'ItemDB',
)

rarity = {
    "Contraband": (8, 0xe4ae39),
    "Exceedingly Rare Item": (7, 0xEB4B4B),
    "Covert": (6, 0xEB4B4B),
    "Classified": (5, 0xD32CE6),
    "Restricted": (4, 0x8847FF),
    "Mil-Spec Grade": (3, 0x4B69FF),
    "Consumer Grade": (2, 0xb0c3d9),
    "Industrial Grade": (1, 0x5e98d9),
}


class ItemDB(ModelPlus):
    name: str
    icon_url: Optional[str]
    rarity: Optional[str]
    price: Optional[float]

    class Config:
        collection = 'items'
        parse_doc_with_default_factories = True

    @root_validator()
    def validate_all(cls, values):
        """
        Item fields can contain the following keys:
            {'rarity', 'tournament', 'souvenir', 'price', 'sticker',
            'gun_type', 'exterior', 'stattrak', 'name', 'icon_url'}
        Since we only care for a few, we purge the rest from the values
        It further validates price to return a float, excepting times when price is
        not specified or invalid type
        """

        def validate_price(p):
            v = 0.0
            try:
                v = float(p)
            except (TypeError, ValueError):
                pass
            finally:
                return v

        d = {k: v for k, v in values.items() if k in ['name', 'icon_url', 'rarity', 'price']}
        d['price'] = validate_price(d.get('price'))

        return d

    @classmethod
    async def get(cls, name: str):
        """Finds an item in the database with the specified name

        Returns:
            Optional[ItemDB]: None if no item was found
        """
        await engine.find_one(cls, cls.name == name)

    def _compare_rarity(self, other: 'ItemDB'):
        """
        Returns a tuple with the rarity value of self and other
        """
        r, _ = rarity[self.rarity]
        ro, _ = rarity[other.rarity]
        return r, ro

    def __lt__(self, other: 'ItemDB'):
        r, ro = self._compare_rarity(other)
        return r < ro

    def __le__(self, other: 'ItemDB'):
        r, ro = self._compare_rarity(other)
        return r <= ro

    def __ge__(self, other: 'ItemDB'):
        r, ro = self._compare_rarity(other)
        return r >= ro

    def __gt__(self, other: 'ItemDB'):
        r, ro = self._compare_rarity(other)
        return r > ro

    def __mul__(self, other: int):
        return self.price * other

    def __add__(self, other: 'ItemDB'):
        return self.price + other.price

    def __radd__(self, other: int):
        return self.price + other
