import json

from .database import Item

with open('etc/new_cases.json') as f:
    all_cases = json.loads(f.read())


class Case:
    def __init__(self, name):
        data = all_cases.get(name, {})
        if not data:
            raise ValueError(f'No case with name "{name}"')

        self.name = data['name']
        self.price = data['price']
        self.items = data['items']
        self.item_names = {item for rarity in self.items.values() for item in rarity}
        self.asset = data['asset']
        self.key = data['key']

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'Case(name={self.name})'

    async def get_items(self):
        return [await Item.from_cache(name) for name in self.item_names]
