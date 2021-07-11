from typing import Optional

from odmantic import Model

from .models import ModelPlus

__all__ = (
    'ItemDB',
)

rarity = {
    "Contraband": (8, 0xe4ae39),
    "Exceedingly Rare Item": (7, 0xEB4B4B),
    "Covert": (6, 0xEB4B4B),
    "Classified": (5, 0xD32CE6),
    "Restricted": (4, 0x8847FF),
    "Mil-Spec Grade": (3, 0x4B69FF),
    "Consumer Grade": (2, 0xb0c3d9),
    "Industrial Grade": (1, 0x5e98d9),
}


class ItemDB(ModelPlus, Model):
    name: str
    icon_url: Optional[str]
    rarity: Optional[str]
    price: Optional[float]

    class Config:
        collection = 'items'

    @property
    def color(self):
        """Returns the color of the item"""
        return rarity[self.rarity][1]

    @property
    def asset_url(self):
        """Returns the asset url for this item"""
        return "https://community.akamai.steamstatic.com/economy/image/" + self.icon_url

    @property
    def rarity_level(self):
        return rarity[self.rarity][0]

    def __lt__(self, other: 'ItemDB'):
        return self.rarity_level < other.rarity_level

    def __le__(self, other: 'ItemDB'):
        return self.rarity_level <= other.rarity_level

    def __ge__(self, other: 'ItemDB'):
        return self.rarity_level > other.rarity_level

    def __gt__(self, other: 'ItemDB'):
        return self.rarity_level >= other.rarity_level

    def __add__(self, other: 'ItemDB'):
        return self.price + other.price

    def __radd__(self, other: int):
        return self.price + other
