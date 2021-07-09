from copy import copy
from datetime import datetime
from typing import List, Dict, Optional

from odmantic import Model, Field, AIOEngine
from odmantic import query
from pydantic import root_validator

engine = AIOEngine(database='casechan')


class ModelPlus(Model):

    @classmethod
    async def get_or_create(cls, **kwargs):
        """
        Searches the collection for a document with specified keys and values
        Args:
            **kwargs: key/values to search for

        Returns:
            The document if found, else a new instance with the attributes set
        Raises:
            AttributeError: If the model does not have the specified attribute set.
            ValidationError: If an object is to be created but required fields are missing
        """
        q = query.and_(*(getattr(cls, kw) == v for kw, v in kwargs.items()))
        doc = await engine.find_one(cls, q)
        return doc or cls(**kwargs)

    async def save(self):
        """
        Persists the instance to the database
        Uses Upsert method
        """
        await engine.save(self)


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

stats_dict = {
    "cases": {
        "received": 0,
        "given": 0,
        "opened": 0
    },
    "keys": {
        "received": 0,
        "given": 0,
    },
    "transactions": {
        "trades_made": 0,
        "items_sold": 0,
        "blocked": False
    }
}


class MemberDB(ModelPlus):
    member_id: int
    guild_id: int
    cases: List = []  # ??
    keys: List = []  # ??
    inventory: Dict[str, int] = {}  # {item_name: quantity}
    stats: dict = copy(stats_dict)
    daily: Optional[datetime] = None
    streak: int = 0
    balance: float = 0.0
    restricted: bool = False

    class Config:
        collection = 'members'

    @classmethod
    def query(cls, *, guild_id: int, member_id: int):
        """
        Since ODMantic's default query dialect is kinda hard to read we simplify it with a classmethod
        """
        return (cls.guild_id == guild_id) & (cls.member_id == member_id)
