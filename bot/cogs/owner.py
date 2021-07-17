from discord import Embed
from discord.ext import commands
from dpytools import Color

from modules.utils import update_item_database


class OwnerCog(commands.Cog, name='owner'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.is_owner()
    @commands.group(hidden=True)
    async def owner(self, ctx):
        pass

    @owner.command(name='update-items', hidden=True)
    async def _update_items(self, ctx):
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


def setup(bot):
    bot.add_cog(OwnerCog(bot))
