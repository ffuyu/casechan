from discord import Embed
from discord.ext import commands
from discord.ext.commands.core import guild_only
from dpytools import Color
from dpytools.checks import is_admin

from modules.database import GuildConfig


class ConfigCog(commands.Cog, name='Configuration'):
    """Set's up the bot's configuration for your server"""
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @is_admin()
    @commands.group(aliases=['set'])
    async def config(self, ctx):
        """Admin restricted, bot configuration commands"""
        pass

    @config.command()
    async def prefix(self, ctx, *, new_prefix: str):
        """
        Sets the new prefix for the server
        Args:
            new_prefix: a sequence of characters to use as the new prefix
        """
        guild_config = await GuildConfig.draw(guild_id=ctx.guild.id)
        guild_config.prefix = new_prefix
        await guild_config.save()
        await ctx.send(embed=Embed(
            description=f'Done, prefix updated to "`{new_prefix}`"',
            color=Color.LIME
        ))

    @guild_only()
    @commands.command(name='prefix')
    async def prefix_(self, ctx):
        """Displays the current prefix in the server"""
        guild = await GuildConfig.get(True, guild_id=ctx.guild.id)
        await ctx.send(f'My prefix in this guild is: "`{guild.prefix}`"')


def setup(bot):
    bot.add_cog(ConfigCog(bot))
