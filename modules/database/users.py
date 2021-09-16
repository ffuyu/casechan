
from .models import ModelPlus
from odmantic import Model

from datetime import datetime, timedelta

from typing import Optional, List

all = {
    'UserData'
}

class UserData(ModelPlus, Model):
    user_id: int
    last_voted: Optional[datetime] = None
    supporter: Optional[bool] = True
    total_votes: int = 0
    acknowledgements: List[str] = []
    created_at: Optional[datetime] = datetime.utcnow()

    class Config: 
        collection = 'users'

    @property
    def vote_expiration(self) -> Optional[datetime]:
        """The optional date on when this user's boost will expire
        Returns:
            Optional[datetime] -> datetime when voting boost will expire
                None if no last_voted
        """
        if self.last_voted:
            return self.last_voted + timedelta(hours=12) 
    
    @property
    def is_boosted(self) -> bool:
        """Boolean that tells if this user is currently boosted
        A boosted user has voted in top.gg at least 12 hours ago
        """
        if self.last_voted:
            return datetime.utcnow() <= self.vote_expiration
 
        return False

    @property
    def is_supporter(self) -> bool:
        """Boolean that tells if this user is currently a supporter"""
        return self.supporter

    @property
    def fees(self) -> float:
        return 0.95 if self.is_boosted or self.supporter else 0.85

    @property
    def multiplier(self) -> int:
        return int(self.is_boosted)+1+int(self.is_supporter)