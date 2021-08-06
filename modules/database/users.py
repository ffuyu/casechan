
from .models import ModelPlus
from odmantic import Model

from datetime import datetime, timedelta

from typing import Optional

all = {
    'User'
}

class User(ModelPlus, Model):
    user_id: int
    last_voted: Optional[datetime] = None
    total_votes: int = 0
    acknowledgements = []
    created_at: Optional[datetime] = datetime.utcnow()

    class Config: 
        collection = 'users'

    @property
    def is_valid(self):
        return datetime.utcnow() <= self.last_voted + timedelta(hours=12) if self.last_voted else False

    @property
    def fees(self):
        return 0.95 if self.is_valid else 0.85
