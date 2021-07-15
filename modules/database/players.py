from copy import copy
from datetime import datetime
from typing import Optional, Dict, List, Tuple

from odmantic import Model, query, EmbeddedModel

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
        "items_sold": 0
    }
}


class Player(ModelPlus, Model):
    member_id: int
    guild_id: int
    cases: Dict[str, int] = {}  # {case.name: number}
    keys: Dict[str, int] = {}  # {key.name: number}
    inventory: Dict[str, List[Tuple[float, int]]] = {}  # {item.name: tuple of stats (float, seed)}
    stats: dict = copy(stats_dict)
    daily: Optional[datetime] = None
    streak: int = 0
    balance: float = 0.0
    restricted: bool = False
    trade_banned: bool = False

    class Config:
        collection = 'players'

    async def inv_items(self) -> List[Item]:
        return await self.engine.find(Item, query.in_(Item.name, [*self.inventory]))

    async def inv_total(self) -> float:
        items = [(i, self.inventory[i.name]) for i in await self.inv_items()]
        return sum([k.price * len(v) for k, v in items])

    def add_item(self, item_name, stats=tuple()):
        if item_name not in self.inventory:
            self.inventory[item_name] = []
        self.inventory[item_name].append(tuple(stats))

    def mod_case(self, case_name, amount: int):
        if case_name not in self.cases:
            self.cases[case_name] = 0

        if self.cases[case_name] + amount < 0:
            self.cases[case_name] = 0
        else:
            self.cases[case_name] += amount

    def mod_key(self, key_name, amount: int):
        if key_name not in self.keys:
            self.keys[key_name] = 0

        if self.keys[key_name] + amount < 0:
            self.keys[key_name] = 0
        else:
            self.keys[key_name] += amount



