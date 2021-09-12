
from modules.database.players import Player
from .models import ModelPlus
from odmantic import Model

from datetime import datetime

from typing import List, Optional, Set

all = {
    'Promo'
}

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
    
    def eligible_for(self, player:Player):
        statements = {
            self.uses < self.max_uses,
            not self.is_expired,
            player.guild_id in self.available_in or not self.available_in,
            player.member_id in self.available_to or not self.available_to,
            player.member_id not in self.users
        }

        return all(statements)