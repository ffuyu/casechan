from discord import Embed
from discord.activity import Game
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import max_concurrency
from dpytools import Color
from dpytools.checks import only_these_users

from modules.config import OWNERS_IDS
from modules.utils import update_item_database


class OwnerCog(commands.Cog, name='owner'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.is_owner()
    @only_these_users(*OWNERS_IDS)
    @commands.group(hidden=True)
    async def owner(self, ctx: Context):
        pass

    @max_concurrency(1, BucketType.default, wait=False)
    @owner.command(name='update-items', hidden=True)
    async def _update_items(self, ctx: Context):
        """Updates the item's database"""
        msg = await ctx.send(embed=Embed(
            description=f"Updating Item's Database...",
            color=Color.YELLOW
        ))
        await update_item_database()
        await msg.edit(embed=Embed(
            description='Done, items updated!',
            color=Color.LIME,
        ), delete_after=60.0)

    @owner.command()
    async def status(self, ctx: Context, *, name: str):
        await self.bot.change_presence(activity=Game(name=name))

def setup(bot):
    bot.add_cog(OwnerCog(bot))
