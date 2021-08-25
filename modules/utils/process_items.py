import asyncio
import logging

from datetime import datetime
from functools import partial
from html import unescape

from aiohttp import ClientSession

from modules.database import Item, engine
from .timer import Timer

__all__ = (
    'update_item_database',
)

log = logging.getLogger(__name__)

_relevant_types = ['Weapon', 'Knife', 'Container']

_relevant_keys = ['name', 'icon_url', 'rarity']
_price_periods = ['7_days', '24_hours', '30_days']
_all_time_stats = ['highest_price', 'average', 'median']


def _select_items_to_persist(items_, db_items_) -> list:
    to_persist = []

    with Timer() as t:
        for nitem in items_:
            it = next(
                (i for i in db_items_ if i.name == nitem['name'] and i.rarity == nitem['rarity']),
                Item(name=nitem['name'], rarity=nitem['rarity'], icon_url=nitem.get('icon_url'))
            )
            if it.price != nitem['price']:
                it.price = nitem['price']
                to_persist.append(it)
    log.info(f'> {len(to_persist)} Need to be persisted to the database. Computing time: {t.t:2f} seconds')
    return to_persist


async def update_item_database():
    """
    Updates the item's database
    """
    items = []

    with Timer() as total_time:
        log.info(f'> Updating item database...')
        with Timer() as t:
            async with ClientSession() as cs:
                async with cs.get("https://csgobackpack.net/api/GetItemsList/v2/?prettyprint=true&details=true") as r:
                    if r.status != 200:
                        log.critical(f'Requesting to API returned status code {r.status} '
                                     f'{datetime.utcnow().strftime("%x %X")}')
                        raise RuntimeError(f'> Status code error {r.status}. Halting')
                    else:
                        res = await r.json()
        log.info(f'Obtained raw items from API. Time: {t.t:.4f}')
        raw_items = list(res['items_list'].values())
        with Timer() as t:
            for raw_item in raw_items:
                if raw_item.get('type') not in _relevant_types:
                    continue
                # debug
                item = {k: v for k, v in raw_item.items() if k in _relevant_keys}
                # get price
                item['name'] = unescape(item.get('name', ''))  # escape html encoded characters
                rprice = raw_item.get('price')

                if rprice:
                    if isinstance(rprice, (float, int)):
                        item['price'] = float(rprice)
                        break
                    for key in _price_periods:
                        if (p := rprice.get(key)) and (ps := float(p['median'])):
                            item['price'] = ps
                            break
                    if 'price' not in item and (at := rprice.get('all_time')):
                        for key in _all_time_stats:
                            if p := at.get(key):
                                item['price'] = float(p)
                                break
                if 'price' not in item:
                    item['price'] = 0.0

                items.append(item)

        log.info(f'Finished processing items Time: {t.t:.4f} seconds. Items: {len(items)}')
        with Timer() as t:
            db_items = await engine.find(Item)
        log.info(f'Getting old items from database took {t.t:.2f} seconds')

        loop = asyncio.get_running_loop()
        to_persist = await loop.run_in_executor(
                None, partial(_select_items_to_persist, items, db_items))

        if to_persist:
            with Timer() as t:
                await engine.save_all(to_persist)
            log.info(f'Database updated. Time: {t.t:.4f} seconds')

    log.info(f'> Script complete. Total time {total_time.t:.2f} seconds')
