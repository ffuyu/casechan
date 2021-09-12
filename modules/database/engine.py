from dotenv.main import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from modules.config import config

import os

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

__all__ = (
    'engine',
)

client = AsyncIOMotorClient(DATABASE_URL) if config.get('DEBUG') != True and DATABASE_URL else None

engine = AIOEngine(motor_client=client, database='casechan')
