import asyncio as aio
import logging

from modules.utils.process_items import update_item_database

logging.basicConfig(level='INFO')
logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")

aio.get_event_loop().run_until_complete(update_item_database())
