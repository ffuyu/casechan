import random
from datetime import datetime, timedelta
from string import ascii_lowercase as abc
from typing import Optional, List
from odmantic import Model, Field, Reference
from odmantic.query import QueryExpression
from pydantic import root_validator

from . import Player, engine
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
    sender_items: list = []
    sender_confirmed: bool = False
    receiver_confirmed: bool = False

    class Config:
        collection = 'trades'

    @root_validator
    def check_guild_id(cls, values):
        """Sets guild_id if necessary"""
        if not values.get('guild_id'):
            p = values.get('sender')
            values['guild_id'] = p.guild_id
        return values

    @root_validator
    def check_expiration_date(cls, values):
        """
        Makes sure expiration date is ahead of creation date
        If expiration date is not specified a date 7 days after creation time will be set
        """
        created_at = values.get('created_at')
        if not values.get('expires_at'):
            values['expires_at'] = created_at + timedelta(days=7)
        if values.get('expires_at') <= created_at:
            raise ValueError('Expiration date comes before or is equal to creation date')
        return values

    @root_validator
    def check_players(cls, values):
        """Makes sure players are not the same"""
        if values.get('sender') == values.get('receiver'):
            raise ValueError('Sender and Receiver players cannot be the same')
        return values

    @classmethod
    async def one_player_trades(cls,
                            player: Player,
                            active: Optional[bool] = None,
                            role: Optional[str] = None,
                            ) -> List['Trade']:
        """
        Returns a list of the specified player's trades
        Args:
            player: a Player instance
            active (Optional[bool]):
                if specified will return trades active (True) or inactive (False)
            role: (Optional[str]):
                Valid values are 'sender' and 'receiver'
                If None:
                    returned list will include any trade where the player is present
                if 'receiver' or 'sender':
                    returned list will include only trades where the player had the specified role
        Returns:
            List[Trade]
        """
        if role is not None:
            if role not in ['sender', 'receiver']:
                raise ValueError(f'Parameter "role" must be "sender" or "receiver" but was {role}')
            q = (cls.receiver == player) if role == 'receiver' else (cls.sender == player)
        else:
            q = (cls.sender == player) | (cls.receiver == player)

        if active is not None:
            if not (t := isinstance(active, bool)):
                raise TypeError(f'Parameter "active" must be bool but was "{t}"')
            q = q & (cls.active.eq(active))

        return await engine.find(cls, q)

    @classmethod
    async def two_player_trades(cls,
                                sender: Player,
                                receiver: Player,
                                active: Optional[bool] = None
                                ) -> List['Trade']:
        """Returns a list of trades with specified sender and receivers"""
        q = cls.sender.eq(sender) & cls.receiver.eq(receiver)

        if active is not None:
            if not (t := isinstance(active, bool)):
                raise TypeError(f'Parameter "active" must be bool but was "{t}"')
            q = q & (cls.active.eq(active))
        return await engine.find(cls, q)

    @classmethod
    async def locate_trade(cls, guild_id: int, code: str) -> Optional['Trade']:
        """Returns a trade """
        q = (cls.guild_id == guild_id) & (cls.code == code)
        return await engine.find_one(cls, q)
