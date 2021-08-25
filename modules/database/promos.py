
from .models import ModelExtMixin
from odmantic import Model

from datetime import datetime

from typing import List, Optional

all = {
    'Promo'
}

class Promo(ModelExtMixin, Model):
    code: str
    expires_at: Optional[datetime] = None
    uses: int = 0
    max_uses: int = 1
    users: List[int] = []
    funds: Optional[int] = 0.00

    class Config: 
        collection = 'promos'

    @property
    def is_expired(self):
        return datetime.utcnow() >= self.expires_at if self.expires_at else False
