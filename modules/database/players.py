from copy import copy
from datetime import datetime
from typing import Optional, Dict, List

from odmantic import Model, query

from .items import Item
from .models import ModelPlus

__all__ = (
    'Player',
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


class Player(ModelPlus, Model):
    member_id: int
    guild_id: int
    cases: List = []  # ??
    keys: List = []  # ??
    inventory: Dict[str, int] = {}  # {item.name: quantity}
    stats: dict = copy(stats_dict)
    daily: Optional[datetime] = None
    streak: int = 0
    balance: float = 0.0
    restricted: bool = False

    class Config:
        collection = 'players'

    async def inv_items(self) -> List[Item]:
        return await self.engine.find(Item, query.in_(Item.name, list(self.inventory)))

    async def inv_total(self) -> float:
        items = [(i, self.inventory[i.name]) for i in await self.inv_items()]
        return sum([k.price * v for k, v in items])
