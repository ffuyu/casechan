import random
from datetime import datetime, timedelta
from string import ascii_lowercase as abc
from typing import Optional, List, Dict, Tuple

from odmantic import Model, Field, Reference
from pydantic import root_validator

from . import Player
from .models import ModelPlus

__all__ = (
    'Trade',
)

"""
{
    "_id": {
        "$oid": "60e5b2e2c4fabdf9080a5694"
    },
    "id": "Px8khH",
    "sender": {
        "$numberLong": "717747572076314745"
    },
    "receiver": {
        "$numberLong": "797161877569798144"
    },
    "created_at": {
        "$date": "2021-07-07T13:57:31.415Z"
    },
    "expires_at": {
        "$date": "2021-07-14T13:57:31.415Z"
    },
    "accepted": false,
    "active": true,
    "sender_items": ["P250 | Sand Dune (Factory New)"],
    "receiver_items": [],
    "confirmed": [{
        "$numberLong": "717747572076314745"
    }]
}
"""


def _random_code():
    chars = abc + '01234567890'
    return ''.join(random.choices(chars, k=6))


class Trade(ModelPlus, Model):
    sender: Player = Reference()
    receiver: Player = Reference()
    guild_id: Optional[int] = None
    code: str = Field(default_factory=_random_code)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # default will be set to +7 days from creation time
    accepted: Optional[bool] = None
    active: bool = True
    sender_items: Dict[str, List[Tuple[float, int]]] = {}  # {item.name: tuple of stats (float, seed)}
    receiver_items: Dict[str, List[Tuple[float, int]]] = {}  # {item.name: tuple of stats (float, seed)}
    sender_confirmed: bool = False
    receiver_confirmed: bool = False

    class Config:
        collection = 'trades'

    @root_validator
    def general_validator(cls, values):
        """Sets guild_id if necessary"""
        if not values.get('guild_id'):
            p = values.get('sender')
            values['guild_id'] = p.guild_id

        created_at = values.get('created_at')
        if not values.get('expires_at'):
            values['expires_at'] = created_at + timedelta(days=7)
        if values.get('expires_at') <= created_at:
            raise ValueError('Expiration date comes before or is equal to creation date')

        if values.get('sender') == values.get('receiver'):
            raise ValueError('Sender and Receiver players cannot be the same')

        return values

    async def _transfer_item(self, target, item_name: str, stats=tuple()):
        """
        Moves items from the target's inventory to the target trade's inventory
        Persists the trade instance and the target instance
        Args:
            target: 'sender' or 'receiver
            item_name: the name of the item
            stats: Tuple[float, seed]
        """
        player = getattr(self, target)
        player.rem_item(item_name, stats)
        target_trade_inv = getattr(self, f'{target}_items')

        item_inv = target_trade_inv.setdefault(item_name, [])
        item_inv.append(tuple(stats))
        await player.save()
        await self.save()

    async def transfer_sender_item(self, item_name: str, stats=tuple()):
        """
        Moves items from the sender's inventory to the sender's trade's inventory
        Persists the trade instance and the target instance
        Args:
            item_name: the name of the item
            stats: Tuple[float, seed]
        """
        await self._transfer_item('sender', item_name, stats)

    async def transfer_receiver_item(self, item_name: str, stats=tuple()):
        """
        Moves items from the receiver's inventory to the receiver's trade's inventory
        Persists the trade instance and the target instance
        Args:
            item_name: the name of the item
            stats: Tuple[float, seed]
        """
        await self._transfer_item('receiver', item_name, stats)

    def _return_item_to_target(self, target, item_name: str, stats=tuple()):
        """Returns specified item from its trade inventory to the player's inventory
        This is not a coroutine, instances will not be persisted
        Args:
            target: 'sender' or 'receiver
            item_name: the name of the item
            stats: Tuple[float, seed]
        """
        """player = getattr(self, target)
        player.rem_item(item_name, stats)
        target_trade_inv = getattr(self, f'{target}_items')

        item_inv = target_trade_inv.setdefault(item_name, [])
        item_inv.append(tuple(stats))
        await player.save()
        await self.save()"""
        player = getattr(self, target)
        target_trade_inv = getattr(self, f'{target}_items')

        item = next((item for item in target_trade_inv.get(item_name, []) if item == stats), None)
        if not item:
            raise ValueError(f'Item {item_name} with stats "{stats}" is '
                             f'not present in the player\'s trade inventory')

        target_trade_inv[item_name].remove(item)
        player.add_item(item_name, item)

    async def cancel(self):
        """
        Cancels the trade and returns any items to their owners.
        It inactivates the trade and saves all instances
        """
        for target in ['sender', 'receiver']:
            for item_name, items in getattr(self, f'{target}_items').items():
                for stats in items:
                    self._return_item_to_target(target, item_name, stats)

        self.active = False
        await self.sender.save()
        await self.receiver.save()
        await self.save()
