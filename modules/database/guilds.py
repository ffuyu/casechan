import logging

from odmantic import Model

from ..constants import DEFAULT_PREFIX

from . import engine
from .models import ModelPlus

__all__ = (
    'GuildConfig',
)

log = logging.getLogger(__name__)

_guilds_cache = {}


class GuildConfig(ModelPlus, Model):
    guild_id: int
    prefix: str = DEFAULT_PREFIX

    class Config:
        collection = 'guilds'

    @classmethod
    async def _refresh_cache(cls):
        global _guilds_cache
        _guilds_cache = {guild_id: g for g in await engine.find(cls)}
        log.info(f'Guild configuration cache updated. {len(_guilds_cache)} guilds in the cache.')

    @classmethod
    async def _cache(cls) -> dict:
        global _guilds_cache
        if not _guilds_cache:
            await cls._refresh_cache()
        return _guilds_cache

    @classmethod
    async def draw(cls, guild_id: int):
        """
        Returns the guild configuration object.
        The steps to get the object are:
            1) checks if it's in the cache
            2) if not in the cache, refreshes the cache.
            3) if still not in the cache then creates a new object and sets it in the cache
        Args:
            guild_id: the discord's snowflake id for that guild
        """
        if guild_id not in _guilds_cache:
            await cls._refresh_cache()
        guild_config = _guilds_cache.setdefault(guild_id, cls(guild_id=guild_id))
        return guild_config

    async def save(self):
        """
        Saves this instance both to the cache and to the database
        """
        cache = await self._cache()
        cache[self.guild_id] = self
        await self.engine.save(self)
        log.info(f'Configuration for guild with id {self.guild_id} persisted to cache and database')
