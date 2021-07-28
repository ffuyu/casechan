from typing import Optional
from asyncio.tasks import wait
from discord.ext.commands.cooldowns import BucketType

from discord.ext.commands.core import max_concurrency
from bot.cogs.core import _case, get_key
from discord import Embed, User
from discord.ext import commands
from discord.ext.commands.context import Context
from dpytools import Color

from modules.utils import update_item_database
from modules.database.players import Player


class OwnerCog(commands.Cog, name='owner'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.is_owner()
    @commands.group(hidden=True)
    async def owner(self, ctx:Context):
        pass

    @owner.command(name='update-items', hidden=True)
    async def _update_items(self, ctx:Context):
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

    @commands.is_owner()
    @commands.group(hidden=True)
    async def user(self, ctx:Context):
        pass

    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def givecase(self, ctx:Context, guild_id:Optional[int], user_id:Optional[int], amount:Optional[int]=1, *, container:Optional[_case]):
        amount = amount if amount > 1 else 1
        """Gives the specified user in specified guild a case and the case key."""
        player = await Player.get(True, member_id=user_id or ctx.author.id, guild_id=guild_id or ctx.guild.id)
        player.mod_case(container, amount)
        player.mod_key(get_key(container), amount)
        await player.save()
        await ctx.send(f"Gave **x{amount} {container}** to **{guild_id or ctx.guild.id}/{user_id or ctx.author}**")

    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def takecase(self, ctx:Context, guild_id:Optional[int], user_id:Optional[int], amount:Optional[int]=-1, *, container:Optional[_case]):
        amount = amount if amount < 0 else -1
        """Gives the specified user in specified guild a case and the case key."""
        player = await Player.get(True, member_id=user_id or ctx.author.id, guild_id=guild_id or ctx.guild.id)
        player.mod_case(container, amount)
        player.mod_key(get_key(container), amount)
        await player.save()
        await ctx.send(f"Took **x{abs(amount)} {container}** from **{guild_id or ctx.guild.id}/{user_id or ctx.author}**")


def setup(bot):
    bot.add_cog(OwnerCog(bot))
