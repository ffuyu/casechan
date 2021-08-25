from asyncio import Lock
from copy import copy
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

from odmantic import Model, query

from modules.database.users import UserData
from .items import Item
from .models import ModelExtMixin

__all__ = (
    'Player',
    'SafePlayer'
)

from ..cases import Case

stats_dict = {
    "cases": {
        "opened": 0
    },
    "transactions": {
        "trades_made": 0,
        "items_sold": 0
    }
}


class Player(ModelExtMixin, Model):
    member_id: int
    guild_id: int
    cases: Dict[str, int] = {}  # {case.name: number}
    keys: Dict[str, int] = {}  # {key.name: number}
    inventory: Dict[str, List[Tuple[float, int]]] = {}  # {item.name: [tuple of stats (float, seed)]}
    inventory_limit: Optional[int] = 1000
    stats: dict = copy(stats_dict)
    daily: Optional[datetime] = datetime.utcnow() - timedelta(days=1)
    hourly: Optional[datetime] = datetime.utcnow() - timedelta(hours=1)
    weekly: Optional[datetime] = datetime.utcnow() - timedelta(weeks=1)
    streak: int = 0  # streak only applies to daily
    balance: float = 0.0
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

    @property
    def inv_items_count(self):
        return sum([self.item_count(x) for x in self.inventory])

    @property
    async def fees(self):
        user = await UserData.get(True, user_id=self.member_id)
        return user.fees

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
            case_name: The name of the case
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

    async def open_case(self, case_name, *, add_item=False):
        """
        Actions:
            -Opens the selected case
            -Adds the generated item to the inventory (if add_item == True)
            -Removes the case and key (if applicable) from the inventory
            -Increases total opened case count (stats)

        Note:
            The player instance is not saved to the database
            After this method you should use `await player.save()`

        Returns:
            Item, (float, seed)
        """

        case = Case(case_name)

        item, *stats = await case.open()

        self.mod_case(case_name, -1)
        self.stats['cases']['opened'] += 1

        if case.key:
            self.mod_key(case.key.name, -1)
        if add_item:
            self.add_item(item.name, stats)

        return item, *stats

    def __str__(self):
        return f'Player(member_id={self.member_id}, guild_id={self.guild_id})'


player_locks = {}


class SafePlayer:
    """
    Context manager that implements asyncio.lock to control access to player documents
    Use:
        async with SafePlayer(member_id, guild_id) as player:
            # work with player
            await player.save()
    """

    def __init__(self, member_id: int, guild_id: int):
        self.mid = member_id
        self.gid = guild_id

    async def __aenter__(self):
        lock = player_locks.setdefault((self.mid, self.gid), Lock())
        self.lock = lock
        await lock.acquire()
        player = await Player.get(True, guild_id=self.gid, member_id=self.mid)
        return player

    async def __aexit__(self, *exc):
        self.lock.release()
