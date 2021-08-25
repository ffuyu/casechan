
from .models import ModelExtMixin
from odmantic import Model

from datetime import datetime, timedelta

from typing import Optional, List

all = {
    'UserData'
}

class UserData(ModelExtMixin, Model):
    user_id: int
    last_voted: Optional[datetime] = None
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
    def fees(self):
        return 0.95 if self.is_boosted else 0.85
