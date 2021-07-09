from typing import Optional

from pydantic import root_validator

from modules.database.engine import engine
from modules.database.models import ModelPlus

__all__ = (
    'ItemDB'
)


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
