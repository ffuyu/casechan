
import asyncio as aio
from modules.database import Item
from modules.cases import all_cases, Case, _generate_item


async def main():
    item_names = [item for case in all_cases.values() for rarity in case['items'] for item in case['items'][rarity]]
    cases = [*all_cases]

    print('making cases')
    for case in cases:
        c = Case(case)
        [await c.open() for _ in range(10)]

l = aio.get_event_loop()
l.run_until_complete(main())