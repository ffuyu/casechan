import random
from typing import Optional, List

from dpytools import Embed
from odmantic import Model

from .engine import engine
from .models import ModelPlus

__all__ = (
    'Item',
)

rarity = {
    "Contraband": (9, 0xe4ae39),
    "Exceedingly Rare Item": (8, 0xEB4B4B),
    "Covert": (7, 0xEB4B4B),
    "Classified": (6, 0xD32CE6),
    "Restricted": (5, 0x8847FF),
    "Mil-Spec Grade": (4, 0x4B69FF),
    "Consumer Grade": (3, 0xb0c3d9),
    "Industrial Grade": (2, 0x5e98d9),
    "Base Grade": (1, 0xb0c3d9)
}

_item_cache = []


def generate_stats(exterior: str):
    ranges = {
        "Battle-Scarred": (0.44, 0.99),
        "Well-Worn": (0.37, 0.439),
        "Field-Tested": (0.85, 0.369),
        "Minimal Wear": (0.07, 0.149),
        "Factory New": (0.00, 0.069)
    }
    range_ = ranges.get(exterior, (0, 0))
    float_ = random.SystemRandom().uniform(a=range_[0], b=range_[1])
    seed = random.SystemRandom().randint(1, 1000)
    return float_, seed


class Item(ModelPlus, Model):
    name: str
    icon_url: Optional[str]
    rarity: Optional[str]
    price: Optional[float]

    class Config:
        collection = 'items'

    @classmethod
    async def from_cache(cls, name: str) -> Optional['Item']:
        """
        Returns an item from the cache instead of querying the database
        If cache hasn't been initiated it is refreshed.
        """
        cache = await cls.item_cache()
        return next((item for item in cache if item.name == name), None)

    @classmethod
    async def _refresh_item_cache(cls):
        global _item_cache
        _item_cache = await engine.find(cls)

    @classmethod
    async def item_cache(cls, *, force_refresh=False):
        if not _item_cache or force_refresh:
            await cls._refresh_item_cache()
        return _item_cache

    @property
    def color(self):
        """Returns the color of the item"""
        if self.rarity == 'Extraordinary':
            r = 'Exceedingly Rare Item'
        else:
            r = self.rarity

        return rarity[r][1]

    @property
    def asset_url(self):
        """Returns the asset url for this item"""
        return ("https://community.akamai.steamstatic.com/economy/image/" + self.icon_url) if self.icon_url else ''

    @property
    def rarity_level(self):
        return rarity[self.rarity][0]

    @property
    def is_marketable(self):
        return True if self.price else False

    @property
    def exterior(self):
        return self.name[self.name.find('(') + 1:self.name.find(')')]

    def to_embed(self, float_=None, seed=None, minimal=False):
        e = Embed(
            description=f"**{self.name}**",
            color=self.color
        ).add_field(name='Price', value=f'${self.price:.2f}', inline=False)

        if self.asset_url:
            e.set_image(url=self.asset_url) if not minimal else e.set_thumbnail(url=self.asset_url)

        if float_:
            e.add_field(name='Float', value=float_, inline=False)
        if seed:
            e.add_field(name='Seed', value=seed, inline=False)

        return e

    def __lt__(self, other: 'Item'):
        return self.rarity_level < other.rarity_level

    def __le__(self, other: 'Item'):
        return self.rarity_level <= other.rarity_level

    def __ge__(self, other: 'Item'):
        return self.rarity_level > other.rarity_level

    def __gt__(self, other: 'Item'):
        return self.rarity_level >= other.rarity_level

    def __add__(self, other: 'Item'):
        return self.price + other.price

    def __radd__(self, other: int):
        return self.price + other


def sort_items(items: List[Item], highest_first: bool = True) -> list:
    sorted_list = sorted(items, key=lambda item: item.price, reverse=highest_first)
    return sorted_list
