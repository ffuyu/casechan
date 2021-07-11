import asyncio
import random
import time

from modules.database import MemberDB, ItemDB, engine


async def main():
    ta = time.monotonic()
    print('Starting Test...')
    r = random.Random(67)

    print('Retrieving or creating member object...')
    m = await MemberDB.get(True, member_id=12345, guild_id=67890)

    print('Selecting 3 random items to give to dummy member...')
    all_items = await engine.find(ItemDB)
    a, b, c = r.sample(all_items, 3)

    print('Updating inventory with selected items...')
    [m.inventory.update({i.name: r.randint(0, 10)}) for i in [a, b, c]]

    print(f'Inventory:\n' + '\n'.join(f'{i}: {c}' for i, c in m.inventory.items()))
    print(f'Inventory value: {await m.inv_total()}')
    print(f'Saving to database...')
    await m.save()
    print(f'Total time: {time.monotonic()-ta:.2f}')

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
