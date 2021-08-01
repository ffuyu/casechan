from odmantic import AIOEngine
import os

__all__ = (
    'engine',
)

DATABASE_URL = os.environ.get('DATABASE_URL')
VM = os.environ.get('VM')
engine = AIOEngine(database='casechan' if not VM else DATABASE_URL)  # engine runs on local database only for the moment.
