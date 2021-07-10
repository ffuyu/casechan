from copy import copy
from datetime import datetime
from typing import Optional, Dict, List

from odmantic import Model

from .models import ModelPlus

__all__ = (
    'MemberDB',
)

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


class MemberDB(ModelPlus, Model):
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
