import json
import random
from copy import copy
from datetime import datetime
from typing import Optional, Dict, List

from odmantic import Model, query

from .items import Item
from .models import ModelPlus

__all__ = (
    'Player',
)

with open('cases.json') as f:
    all_cases = json.loads(f.read())

stats_dict = {
    "cases": {
        "received": 0,
        "given": 0,
        "opened": 0
    },
    "keys": {
        "received": 0,
        "given": 0,
    },
    "transactions": {
        "trades_made": 0,
        "items_sold": 0,
        "blocked": False
    }
}


class Player(ModelPlus, Model):
    member_id: int
    guild_id: int
    cases: List = []  # ??
    keys: List = []  # ??
    inventory: Dict[str, int] = {}  # {item.name: quantity}
    stats: dict = copy(stats_dict)
    daily: Optional[datetime] = None
    streak: int = 0
    balance: float = 0.0
    restricted: bool = False

    class Config:
        collection = 'players'

    async def inv_items(self) -> List[Item]:
        return await self.engine.find(Item, query.in_(Item.name, list(self.inventory)))

    async def inv_total(self) -> float:
        items = [(i, self.inventory[i.name]) for i in await self.inv_items()]
        return sum([k.price * v for k, v in items])

    @property
    def _rarities(self):
        """
        Returns the dictionary of grade's names and weights
        Because this class is a Model, this cannot be a class variable, it has to be a property
        """
        return {  # grade weight, st weight 1 & 2
            "Mil-Spec Grade": (79.92327, 92.00767, 7.99233),
            "Restricted": (15.98465, 98.40153, 1.59847),
            "Classified": (3.19693, 99.68031, 0.31969),
            "Covert": (0.63939, 99.93606, 0.06394),
            "Exceedingly Rare Item": (0.25575, 99.97442, 0.02558),
        }

    def generate_item(self, case_name: str, rarity: str):
        rarities = self._rarities

        item_name = random.choice(all_cases[case_name][rarity])

        float_ = 0.0
        if '|' in item_name:
            exterior_dist = {  # weight, uniform a, uniform b.
                "Factory New": (3, 0.00, 0.069),
                "Minimal Wear": (24, 0.07, 0.149),
                "Field-Tested": (33, 0.15, 0.369),
                "Well-Worn": (24, 0.37, 0.439),
                "Battle-Scarred": (16, 0.44, 1),
            }
            exterior = random.choices([*exterior_dist], weights=[w for w, *_ in exterior_dist.values()], k=1)[0]
            _, a, b = exterior_dist[exterior]
            float_ = random.uniform(a, b)
            item_name += f' ({exterior})'

        if not any([k in item_name for k in ['Gloves', 'Wraps']]):
            # Generate StatTrak™ if not a glove item
            # 0 = Item is not StatTrak™
            # 1 = Item is StatTrak™
            _, z, o = rarities[rarity]
            st = random.choices([0, 1], weights=(z, o), k=1)[0]
            if st:
                item_name = f'StatTrak™ {item_name}'

        if rarity == "Exceedingly Rare Item":
            item_name = f"★ {item_name}"

        return item_name, float_

    async def open_case(self, case_name):
        rarities = self._rarities
        rarity = random.choices([*rarities], weights=[v for v, *_ in rarities.values()], k=1)[0]

        items = await self.engine.find(Item, Item.query(rarity=rarity))
        print([it.name for it in items if 'Gloves' in it.name])
        item_name, float_ = '', 0.0
        valid_item_names = [item.name for item in items]
        counter = 0
        while item_name not in valid_item_names and counter < 100:
            item_name, float_ = self.generate_item(case_name, rarity)
            counter += 1

        item = next((it for it in items if it.name == item_name), None)
        if not item:
            raise Exception(f'{item_name} could not be associated to any valid item.')
        print(item)
        return item, float_



