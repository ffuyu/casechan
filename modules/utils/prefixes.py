from discord.ext import commands

from modules.config import config
from modules.database import Guild

__all__ = (
    'get_command_prefix',
)

DEFAULT_PREFIX = config.get('default_prefix')

async def get_command_prefix(bot, message):
    """
    Used by the bot to get the prefix for the guild.
    """
    if message.guild:
        guild_config = await Guild.draw(guild_id=message.guild.id)
        prefix = guild_config.prefix
    else:
        prefix = DEFAULT_PREFIX
    return commands.when_mentioned_or(f"{prefix} ", prefix)(bot, message)
