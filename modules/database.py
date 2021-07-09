from copy import copy
from datetime import datetime
from typing import List, Dict

from odmantic import Model, Field, AIOEngine
from pydantic import root_validator

engine = AIOEngine(database='casechan')

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


class ItemDB(Model):
    name: str
    icon_url: str
    rarity: str
    price: float = Field(default_factory=lambda x: float(x) if x else 0.0)

    class Config:
        collection = 'items'

    @root_validator()
    def validate_fields(cls, values):
        """
        Item fields can contain the following keys:
            {'rarity', 'tournament', 'souvenir', 'price', 'sticker',
            'gun_type', 'exterior', 'stattrak', 'name', 'icon_url'}
        Since we only care for a few, we purge the rest from the values
        """
        return {k: v for k, v in values.items() if k in ['name', 'icon_url', 'rarity', 'price']}


class MemberDB(Model):
    member_id: int
    guild_id: int
    cases: List = []  # ??
    keys: List = []  # ??
    inventory: Dict[str, int]  # {item_name: quantity}
    stats: dict = Field(default_factory=lambda: copy(stats_dict))
    daily: datetime = None
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

    @classmethod
    async def get_or_create(cls, guild_id: int, member_id: int):
        q = cls.query(guild_id=guild_id, member_id=member_id)
        m = await engine.find_one(cls, q)
        return m or cls(member_id=member_id, guild_id=guild_id)

    async def save(self):
        await engine.save(self)
