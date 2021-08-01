from dotenv.main import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
import os

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

__all__ = (
    'engine',
)

client = AsyncIOMotorClient(DATABASE_URL)

engine = AIOEngine(motor_client=client, database='casechan')  # engine runs on local database only for the moment.
