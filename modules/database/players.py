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

    def _mod_case_or_key(self, attr_name, name, n: int):
        """
        Private method for modifying cases or keys
        Args:
            attr_name: 'cases' or 'keys'
            name: name of the key
            n: amount to modify it with
        """
        attr = getattr(self, attr_name)
        attr.setdefault(name, 0)
        attr[name] += n
        if attr[name] <= 0:
            del attr[name]

    def mod_case(self, case_name, n: int = 1):
        """
        Modifies the amount of keys in the player's inventory.
        Same as self.mod_case but, for keys
        Args:
            key_name: The name of the key
            n: amount to modify the inventory with
        Returns:
            None
        """
        self._mod_case_or_key('cases', case_name, n)

    def mod_key(self, key_name, n: int = 1):
        """
        Modifies the amount of keys in the player's inventory.
        Same as self.mod_case but, for keys
        Args:
            key_name: The name of the key
            n: amount to modify the inventory with
        Returns:
            None
        """
        self._mod_case_or_key('keys', key_name, n)


