from copy import copy
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

from odmantic import Model, query, EmbeddedModel, Reference

from .items import Item
from .models import ModelPlus

__all__ = (
    'Player',
)

stats_dict = {
    "cases": {
        "opened": 0
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
    inventory: Dict[str, List[Tuple[float, int]]] = {}  # {item.name: [tuple of stats (float, seed)]}
    stats: dict = copy(stats_dict)
    daily: Optional[datetime] = datetime.utcnow() - timedelta(days=1)
    hourly: Optional[datetime] = datetime.utcnow() - timedelta(hours=1)
    weekly: Optional[datetime] = datetime.utcnow() - timedelta(weeks=1)
    streak: int = 0
    balance: float = 0.0
    restricted: bool = False
    trade_banned: bool = False
    created_at: datetime = datetime.utcnow()

    class Config:
        collection = 'players'

    async def get_item_variants_embeds(self, item_name: str, minimal: bool = False):
        """Gets a list of embeds each corresponding to an item variant present in the player's inventory
        Args:
            item_name: the name of the item to look for
            minimal (bool): whether to return the minimal thumbnail or full image
        """
        all_stats = self.inventory[item_name]
        item = await Item.get(name=item_name)
        embeds = [
            item.to_embed(*stats, minimal)
            for stats in all_stats
        ]
        return embeds

    async def get_item_embed(self, item_name: str, stats=tuple(), minimal: bool = False):
        """Gets back an inventory item embed"""
        if stats not in self.inventory[item_name]:
            raise ValueError(f'No "{item_name}" with stats "{stats}" '
                             f'found in the player\'s inventory')
        item = await Item.get(name=item_name)
        return item.to_embed(*stats, minimal)

    async def inv_items(self) -> List[Item]:
        return await self.engine.find(Item, query.in_(Item.name, [*self.inventory]))
    
    def inv_items_count(self):
        return sum([self.item_count(x) for x in self.inventory])

    async def inv_total(self) -> float:
        items = [(i, self.inventory[i.name]) for i in await self.inv_items()]
        return sum([k.price * len(v) for k, v in items])

    def add_item(self, item_name, stats=tuple()):
        item_inv = self.inventory.setdefault(item_name, [])
        item_inv.append(tuple(stats))

    def rem_item(self, item_name, stats=tuple()):
        """Removes an item from the user's inventory
        Args:
            item_name: the name of the item to remove
            stats: The stats of the specific item to remove
                If no stats are specified then an empty tuple will be used
        Raises:
            ValueError:
                If no item is present with selected name or stats
        """
        item = next((item for item in self.inventory.get(item_name, []) if item == stats), None)
        if not item:
            raise ValueError(f'Item {item_name} with stats "{stats}" is '
                             f'not present in the player\'s inventory')

        self.inventory[item_name].remove(item)

        if not self.inventory[item_name]:
            self.inventory.pop(item_name)

    def item_count(self, item_name):
        inv = self.inventory.get(item_name, [])
        return len(inv)

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
