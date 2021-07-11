import asyncio
import time

import requests

from modules.database import ItemDB, engine

print('starting up')
print('> Requesting...')
a = time.monotonic()
r = requests.get("https://csgobackpack.net/api/GetItemsList/v2/?prettyprint=true&details=true")
b = time.monotonic()
print(f'Request finished. Time: {b - a:.4f} seconds')
if r.status_code != 200:
    print(f'> Status code error {r.status_code}. Exiting...')
    exit(1)

print('> Converting response object to list of raw items...')
b = time.monotonic()
res = r.json()
raw_items = list(res['items_list'].values())
c = time.monotonic()
print(f'Finished. Time: {c - b:.2f}. Total items {len(raw_items)}')

print('> Processing items...')

b = time.monotonic()
items = []
relevant_rarities = ['Contraband', 'Covert', 'Classified', 'Restricted',
                     'Mil-Spec Grade', 'Consumer Grade', 'Industrial Grade']
relevant_keys = ['name', 'icon_url', 'rarity']
price_periods = ['7_days', '24_hours', '30_days']
all_time_stats = ['highest_price', 'average', 'median']
for ri in raw_items:
    if ri.get('rarity') not in relevant_rarities:
        continue
    item = {k: v for k, v in ri.items() if k in relevant_keys}
    # get price
    rprice = ri.get('price')
    if rprice:
        for key in price_periods:
            if p := rprice.get(key):
                item['price'] = float(p['median'])
                break
        if 'price' not in item and (at := rprice.get('all_time')):
            for key in all_time_stats:
                if p := at.get(key, False):
                    item['price'] = float(p)
                    break
    if 'price' not in item:
        item['price'] = 0.0

    items.append(item)

c = time.monotonic()
print(f'Finished. Time: {c - b:.2f}. Items: {len(items)}')


async def persist_items(items_):
    to_persist = []

    async def get_from_db(nitem_):
        it = await ItemDB.get(True, name=nitem_['name'], rarity=nitem_['rarity'])
        if it.price != nitem_['price']:
            it.price = nitem_['price']
            to_persist.append(it)

    print('> Selecting items from the database that require updating...', flush=True)
    b = time.monotonic()

    await asyncio.gather(
        *[get_from_db(nitem) for nitem in items_]
    )

    print(f'Database items that need to be updated: {len(to_persist)}')
    if to_persist:
        print('Updating database...')
        await engine.save_all(to_persist)

    c = time.monotonic()
    print(f'Done. Time: {c - b:.2f}')


loop = asyncio.get_event_loop()
loop.run_until_complete(persist_items(items))

b = time.monotonic()
print(print(f'> Script complete. Total time {b - a:.2f} seconds'))
exit(0)
