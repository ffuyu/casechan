import asyncio
import concurrent.futures
import json
import random
from functools import partial

from modules.database import Item

__all__ = (
    'open_case',
    'all_cases',
    'all_collections',
    'case_assets',
    'Case',
)

with open('etc/cases.json', encoding='utf-8') as f:
    all_cases = json.loads(f.read())
    all_keys = ['{} Key'.format(x) for x in all_cases]

with open("etc/collections.json", "r", encoding='utf-8') as f:
    all_collections = json.loads(f.read())

with open('etc/case_assets.json', 'r', encoding='utf-8') as f:
    case_assets = json.loads(f.read())

_rarities = {  # grade weight, st weight 1 & 2
    "Mil-Spec Grade": (79.92327, 92.00767, 7.99233),
    "Restricted": (15.98465, 98.40153, 1.59847),
    "Classified": (3.19693, 99.68031, 0.31969),
    "Covert": (0.63939, 99.93606, 0.06394),
    "Exceedingly Rare Item": (0.25575, 99.97442, 0.02558),
}


def _generate_item(container_name: str, data: dict):
    rarities = _rarities
    possible_rarities = {k: v for k, v in rarities.items() if k in data[container_name]}
    rarity = random.choices(population=[*possible_rarities],
                            weights=[v for v, *_ in possible_rarities.values()],
                            k=1)[0]

    item_name = random.choice(data[container_name][rarity])

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

    seed = random.randint(1, 1000)

    return item_name, float_, seed


def _get_valid_item(valid_item_names, container_name, data):
    item_name, float_, seed = '', 0.0, 1
    while item_name not in valid_item_names:
        item_name, float_, seed = _generate_item(container_name, data)
    return item_name, float_, seed


async def open_case(container_name, type_='case'):
    """
    Args:
        container_name:
        type_: 'case' or 'collection'
    Returns:
        generated item and float
    """
    try:
        data = {'case': all_cases, 'collection': all_collections}[type_]
    except KeyError:
        raise ValueError(f'type_ must be either "case" or "collection" but was "{type_}"')

    items = await Item.item_cache()

    valid_item_names = [item.name for item in items]

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, partial(
            _get_valid_item, valid_item_names, container_name, data))

    item_name, float_, seed = result

    item = next((it for it in items if it.name == item_name), None)

    return item, float_, seed


class Case:
    def __init__(self, name: str):
        if name not in all_cases:
            raise ValueError(f'"{name}" is not a valid case name')
        self.name = name
        self.asset = case_assets[name]
        self.items = all_cases[name]
        self.key = '{} Key'.format(name)

    def __str__(self):
        return self.name

    async def open(self):
        return await open_case(container_name=self.name)

class Key:
    def __init__(self, name: str):
        if name not in all_keys:
            raise ValueError(f'"{name}" is not a valid key name')
        self.name = name
        self.case = Case(self.name.replace(' Key', ''))

    def __str__(self):
        return self.name

    async def use(self):
        return await open_case(container_name=self.case.name)

