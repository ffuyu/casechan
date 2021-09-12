import logging
from typing import Optional

from odmantic import Model

from . import engine, Player
from .models import ModelPlus

from modules.config import config

__all__ = (
    'Guild',
)

log = logging.getLogger(__name__)

_guilds_cache = {}

DEFAULT_PREFIX = config.get('default_prefix')

class Guild(ModelPlus, Model):
    # Stores guild information and configuration
    # Hence the name Guild, this model must be imported
    # as Guild_ in files that also import discord.Guild 
    # to prevent conflicts.

    guild_id: int
    prefix: str = DEFAULT_PREFIX
    
    # whether to exclude the server from global leaderboards
    # this variable alone does not determine the exclusion
    # and exclusion must be checked through @is_excluded
    excluded_from_leaderboards: bool = False

    # whether if guild is allowed to appear on casechan.com/profile and if 
    # user profiles in this guild are allowed to be fetched through profile URLs
    excluded_from_web: bool = False

    # allow server administrators to distribute cases, keys and create promotion codes for the server
    server_cheats_enabled: bool = False

    @property
    def is_excluded(self) -> bool:
        # Auto exclude if server has cheats enabled
        return self.excluded_from_leaderboards or self.server_cheats_enabled

    @property
    async def total_worth(self) -> float:
        if players:=await engine.find(Player, Player.guild_id == self.guild_id):return sum([await player.inv_total() for player in players]) if players else 0.00

    class Config:
        collection = 'guilds'

    @classmethod
    async def _refresh_cache(cls):
        global _guilds_cache
        _guilds_cache = {g.guild_id: g for g in await engine.find(cls)}
        log.info(f'Guild config refreshed')

    @classmethod
    async def _cache(cls) -> dict:
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
        if not _guilds_cache:
            await cls._refresh_cache()
        guild_config = _guilds_cache.setdefault(guild_id, cls(guild_id=guild_id))
        return guild_config

    async def save(self):
        """
        Saves this instance both to the cache and to the database
        """
        _guilds_cache[self.guild_id] = self
        await self.engine.save(self)
        log.info(f'Configuration for guild with id {self.guild_id} persisted to cache and database')
