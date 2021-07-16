import asyncio
import logging
from datetime import datetime

import requests

from modules.database import Item, engine
from .timer import Timer

__all__ = (
    'update_item_database',
)

log = logging.getLogger(__name__)

relevant_rarities = ['Contraband', 'Covert', 'Classified', 'Restricted',
                     'Mil-Spec Grade', 'Consumer Grade', 'Industrial Grade',
                     'Extraordinary']

relevant_keys = ['name', 'icon_url', 'rarity']
price_periods = ['7_days', '24_hours', '30_days']
all_time_stats = ['highest_price', 'average', 'median']


async def _persist_items(items):
    to_persist = []
    db_items = await engine.find(Item)

    log.info('Persisting new item data to database')
    with Timer() as t:
        for nitem in items:
            it = next(
                (i for i in db_items if i.name == nitem['name'] and i.rarity == nitem['rarity']),
                Item(name=nitem['name'], rarity=nitem['rarity'], icon_url=nitem.get('icon_url'))
            )
            if it.price != nitem['price']:
                it.price = nitem['price']
                to_persist.append(it)

        if to_persist:
            await engine.save_all(to_persist)

    log.info(f'Database updated. Items persisted {len(to_persist)}. Time: {t.t:.4f} seconds')


def update_item_database(loop=None):
    """
    Updates the item's database
    Part of this function runs asynchronous using the an asyncio loop either specified or from asyncio.get_event_loop
    It should be run before starting the bot.

    Args:
        loop: optional the asyncio loop to use for persisting database items
    """
    items = []

    with Timer() as total_time:
        log.info(f'> Updating items database...')
        with Timer() as t:
            r = requests.get("https://csgobackpack.net/api/GetItemsList/v2/?prettyprint=true&details=true")
        log.info(f'Requesting data done. Time: {t.t:.2f} seconds')

        if r.status_code != 200:
            log.critical(f'Requesting to API returned status code {r.status_code} '
                         f'{datetime.utcnow().strftime("%x %X")}')
            raise RuntimeError(f'> Status code error {r.status_code}. Halting')

        res = r.json()
        raw_items = list(res['items_list'].values())
        log.info('Processing received items')
        with Timer() as t:
            for raw_item in raw_items:
                if raw_item.get('rarity') not in relevant_rarities:
                    continue
                item = {k: v for k, v in raw_item.items() if k in relevant_keys}
                # get price
                rprice = raw_item.get('price')
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

        log.info(f'Finished processing items Time: {t.t:.4f} seconds. Items: {len(items)}')
        if not loop:
            loop = asyncio.get_event_loop()
        loop.run_until_complete(_persist_items(items))

    log.info(f'> Script complete. Total time {total_time.t:.2f} seconds')


