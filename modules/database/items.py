from typing import Optional

from dpytools import Embed
from odmantic import Model

from .engine import engine
from .models import ModelPlus

__all__ = (
    'Item',
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

_item_cache = []


class Item(ModelPlus, Model):
    name: str
    icon_url: Optional[str]
    rarity: Optional[str]
    price: Optional[float]

    class Config:
        collection = 'items'

    @classmethod
    async def _refresh_item_cache(cls):
        global _item_cache
        _item_cache = await engine.find(cls)

    @classmethod
    async def item_cache(cls, *, force_refresh=False):
        global _item_cache
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

    def to_embed(self, float_=None, seed=None):
        e = Embed(
            title=self.name,
            color=self.color
        ).add_field(name='Price', value=f'${self.price:.4f}', inline=False)
        if self.asset_url:
            e.set_image(url=self.asset_url)

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
