from modules.errors import ForbiddenAmount
from discord.colour import Colour
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.core import max_concurrency
from discord import Guild, User
from discord.ext.commands.errors import MissingPermissions, NotOwner

from dpytools.embeds import *

from typing import Optional

from modules.config import OWNERS_IDS

from modules.utils.case_converter import ContainerConverter
from modules.cases import Case
from modules.database.players import SafePlayer
from modules.database import Guild as Guild_

async def has_admin_in_cheats_enabled_server_or_owner(guild, ctx):
    # if guild is not specified or the specified guild is the current guild | giving to the current guild | requires administrator permission
    if not guild or guild == ctx.guild and not ctx.author.guild_permissions.administrator: raise MissingPermissions(['administrator'])
    # if guild is specified and the specified guild is not the current guild | giving to another guild | requires bot ownership
    if guild and guild != ctx.guild and not ctx.author.id in OWNERS_IDS: raise NotOwner('You are not allowed to perform this action.')
    
    
    guild_ = await Guild_.get(True, guild_id=ctx.guild.id if not guild else guild.id)
    if not guild_.server_cheats_enabled and not ctx.author.id in OWNERS_IDS: raise NotOwner('Can\'t perform this action on servers with cheats disabled.')

    return True

async def _alter_case(ctx: Context,
                      amount: int,
                      container: Case,
                      msg: str,
                      guild_id: Optional[int] = None,
                      user_id: Optional[int] = None,
                      ):
    """Handles the logic to modify cases for specified user"""
    guild_id = guild_id or ctx.guild.id
    user_id = user_id or ctx.author.id
    async with SafePlayer(user_id or ctx.author.id, guild_id or ctx.guild.id) as player:
        player.mod_case(container.name, amount)
        player.mod_key(container.key.name, amount)
        await player.save()
    await ctx.send(msg)

class UsersCog(commands.Cog, name='Users'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.group(hidden=True)
    async def user(self, ctx:Context):
        pass

    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def givecase(self, ctx:Context, guild:Optional[Guild], user:Optional[User], amount:Optional[int]=1, *, container:Optional[ContainerConverter]):
        """Gives the specified user in specified guild a case and the case key."""
        
        if not await has_admin_in_cheats_enabled_server_or_owner(guild or ctx.guild, ctx): return
        if not ctx.author.id in OWNERS_IDS and amount > 1000: raise ForbiddenAmount('You can only give 1000 cases at once')

        container: Case()
        if container:
            guild = guild or ctx.guild
            user = user or ctx.author
            amount = amount if amount > 1 else 1
            msg = f"Gave **x{amount} {container}** to **{guild.id or ctx.guild.id}/{user.id or ctx.author}**"
            return await _alter_case(ctx, amount, container, msg, guild.id, user.id)
        await ctx.send('Specified case could not be found')
        

    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def ban(self, ctx:Context, guild:Optional[Guild], user:Optional[Guild]):
        """Applies a permanent trade-ban to player in specified guild"""

        if not await has_admin_in_cheats_enabled_server_or_owner(guild or ctx.guild, ctx): return

        guild = guild or ctx.guild
        user = user or ctx.author
        async with SafePlayer(user.id, guild.id) as player:
            player.trade_banned = True
            await player.save()
        await ctx.send(f"**{guild.id or ctx.guild.id}/{user.id or ctx.author}** has been trade banned permanently.")

    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def unban(self, ctx:Context, guild:Optional[Guild], user:Optional[User]):
        
        if not await has_admin_in_cheats_enabled_server_or_owner(guild or ctx.guild, ctx): return

        """Removes trade restrictions from a player"""
        guild = guild or ctx.guild
        user = user or ctx.author
        async with SafePlayer(user.id, guild.id) as player:
            player.trade_banned = False
            await player.save()
        await ctx.send(f"Removed trade restrictions from **{guild.id or ctx.guild.id}/{user.id or ctx.author}**.")

    @commands.is_owner()
    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def delete(self, ctx: Context, guild_id: Optional[int], user_id:Optional[int]):
        """
        Deletes a user from the database
        """
        async with SafePlayer(user_id or ctx.author.id, guild_id or ctx.guild.id) as player:
            await player.delete()
        await ctx.send(f"**{guild_id or ctx.guild.id}/{user_id or ctx.author.id}** has been deleted from database.")


def setup(bot):
    bot.add_cog(UsersCog(bot))