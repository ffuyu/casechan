from modules.errors import AlreadyClaimed, CodeExpired, CodeInvalid, ReachedMaxUses

from modules.database.players import Player
from .models import ModelPlus
from odmantic import Model

from datetime import datetime

from typing import List, Optional

__all__ = (
    'Promo'
)

class Promo(ModelPlus, Model):
    # the actual code player has to specify to receive funds
    code: str
    # expiration date for this promo code
    expires_at: Optional[datetime] = None
    # total uses of this promo code, can get using len(users)
    uses: int = 0
    # amount this promo can be used, once equal with uses, cannot be claimed anymore
    max_uses: int = 1
    # people who had used this code | prevents a user from claiming the same code in another guild
    users: List[int] = []
    # funds given to user on claim
    funds: Optional[int] = 0.00

    # guilds that can use this promo code, empty array means any guild can use
    is_global: bool = False

    available_in: Optional[list] = []

    # users who can use this promo code, empty array means anyone can use if global or in given available_in
    available_to: Optional[list] = []

    class Config: 
        collection = 'promos'

    @property
    def is_expired(self):
        return datetime.utcnow() >= self.expires_at if self.expires_at else False
    
    def eligible_for(self, player:Player) -> Optional[bool]:
        if self.uses >= self.max_uses:raise ReachedMaxUses('This promo code has reached max uses.')
        if self.is_expired:raise CodeExpired('This promo code has expired.')
        if self.available_in and player.guild_id not in self.available_in: raise CodeInvalid('This promo code is not valid in this server.')
        if self.available_to and player.member_id not in self.available_to: raise CodeInvalid('You are not allowed to redeem this promo code.')
        if player.member_id in self.users: raise AlreadyClaimed('You have already redeemed this promo code.')

        return True