import asyncio
import concurrent.futures
import json
import random
from functools import partial

from modules.database import Item

with open('etc/cases.json') as f:
    all_cases = json.loads(f.read())

with open("etc/collections.json", "r", encoding='utf-8') as f:
    all_collections = json.loads(f.read())


class Case:
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

    def generate_item(self, container_name: str, data: dict):
        rarities = self._rarities
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

        return item_name, float_

    def get_valid_item(self, valid_item_names, container_name, data):
        item_name, float_ = '', 0.0
        while item_name not in valid_item_names:
            item_name, float_ = self.generate_item(container_name, data)
        return item_name, float_

    async def open_case(self, container_name, type_='case'):
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
                self.get_valid_item, valid_item_names, container_name, data))
        item_name, float_ = result

        item = next((it for it in items if it.name == item_name), None)

        return item, float_
