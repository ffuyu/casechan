from discord.ext import commands

from modules.constants import DEFAULT_PREFIX
from modules.database import GuildConfig

__all__ = (
    'get_command_prefix',
)


async def get_command_prefix(bot, message):
    """
    Used by the bot to get the prefix for the guild.
    """
    if message.guild:
        guild_config = await GuildConfig.draw(guild_id=message.guild.id)
        prefix = guild_config.prefix
    else:
        prefix = DEFAULT_PREFIX
    return commands.when_mentioned_or(f"{prefix} ", prefix)(bot, message)
