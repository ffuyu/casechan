from odmantic import AIOEngine

__all__ = (
    'engine',
)

engine = AIOEngine(database='casechan') # engine runs on local database only for the moment.
