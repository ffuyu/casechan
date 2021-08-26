import asyncio
import json
import logging
import random
from functools import partial

from .constants import KEY_PRICE
from .database import Item
from .errors import FailedItemGen

log = logging.getLogger(__name__)

with open('etc/cases.json') as f:
    all_cases = json.loads(f.read())
    all_keys = [key for c in all_cases if (key := all_cases[c]['key'])]

_rarities = {  # grade weight, st weight 1 & 2
    "Mil-Spec Grade": (79.92327, 92.00767, 7.99233),
    "Restricted": (15.98465, 98.40153, 1.59847),
    "Classified": (3.19693, 99.68031, 0.31969),
    "Covert": (0.63939, 99.93606, 0.06394),
    "Exceedingly Rare Item": (0.25575, 99.97442, 0.02558),
}

_exterior_dist = {  # weight, uniform a, uniform b.
    "Factory New": (3, 0.00, 0.069),
    "Minimal Wear": (24, 0.07, 0.149),
    "Field-Tested": (33, 0.15, 0.369),
    "Well-Worn": (24, 0.37, 0.439),
    "Battle-Scarred": (16, 0.44, 1),
}


def _generate_item(item_name, rarity, valid_exteriors):
    float_ = 0.0

    if valid_exteriors and '|' in item_name:
        exts, weights = zip(*((k, v[0]) for k, v in _exterior_dist.items() if k in valid_exteriors))
        exterior = random.choices(exts, weights=weights, k=1)[0]
        _, a, b = _exterior_dist[exterior]
        float_ = random.uniform(a, b)
        item_name += f' ({exterior})'

    if all(k not in item_name for k in ['Gloves', 'Wraps']):
        # Generate StatTrak™ if not a glove item
        # 0 = Item is not StatTrak™
        # 1 = Item is StatTrak™
        _, z, o = _rarities[rarity]
        st = random.choices([0, 1], weights=(z, o), k=1)[0]
        if st:
            item_name = f'StatTrak™ {item_name}'

    if rarity == "Exceedingly Rare Item":
        item_name = f"★ {item_name}"

    seed = random.randint(1, 1000)

    return item_name, float_, seed


def _get_valid_item(item_name, rarity, valid_items, valid_exteriors):
    item, float_, seed = None, 0.0, 0
    i = 0
    while item not in valid_items:
        item_n, float_, seed = _generate_item(item_name, rarity, valid_exteriors)
        item = next((i for i in valid_items if item_n == i.name), None)
        if not item:
            i += 1
            log.warning(f'Failed to generate item (try {i}): "{item_name}" converted to "{item_n}"')
            if i == 10:
                raise FailedItemGen(f'Failed to generate item after 10 trials: '
                                    f'"{item_name}" | {rarity} | {valid_items} | '
                                    f'{valid_exteriors} converted to "{item_n}"')
    return item, float_, seed


class Case:
    _items_cache = {}

    def __init__(self, name: str):
        data = all_cases.get(name, {})
        if not data:
            raise ValueError(f'No case with name "{name}"')

        self.name = data['name']
        self.price = data['price']
        self.asset = data['asset']

        self.items = data['items']
        self.item_names = {item for rarity in self.items.values()
                           for item in rarity}
        self.item_rarities = {*self.items}

        self._key = data['key']

    @property
    def key(self):
        return Key(self._key) if self._key else None

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'Case(name={self.name})'

    async def get_items(self):
        if not self._items_cache.get(self.name):
            items_cache = set(await Item.item_cache())
            case_cache = set()
            for item_name in self.item_names:
                case_cache.update([item for item in items_cache
                                   if item_name in item.name])
            cache = self._items_cache.setdefault(self.name, set())
            cache.update(case_cache)
        return self._items_cache[self.name]

    async def open(self):
        """Opens this case and returns an item and its stats"""
        rarities, weights = zip(*((k, v[0]) for k, v in _rarities.items() if k in self.item_rarities))
        rarity = random.choices(population=rarities, weights=weights, k=1)[0]

        item_name = random.choice(self.items[rarity])
        valid_items = {item for item in await self.get_items()
                       if item_name in item.name}

        exteriors = {it.exterior for it in valid_items if it.exterior}

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            partial(_get_valid_item, item_name, rarity, valid_items, exteriors)
        )

        return result


class Key:
    def __init__(self, name):
        self.case = Case(name[:-4])
        self.name = name
        self.price = KEY_PRICE

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'Key(name={self.name})'

    async def use(self):
        return await self.case.open()
