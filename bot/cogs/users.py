from discord.colour import Colour
from discord.embeds import Embed
from dpytools.checks import only_these_users
from modules.utils.case_converter import CaseConverter
from typing import Optional
from modules.database.players import Player
from discord.ext import commands
from discord.ext.commands.context import Context
from modules.cases import Case
from discord.ext.commands.core import max_concurrency
from discord import Guild, User
from modules.constants import owners_ids

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
    player = await Player.get(True, member_id=user_id or ctx.author.id, guild_id=guild_id or ctx.guild.id)
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

    @commands.is_owner()
    @only_these_users(*owners_ids)
    @commands.group(hidden=True)
    async def user(self, ctx:Context):
        pass

    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def givecase(self, ctx:Context, guild:Optional[Guild], user:Optional[User], amount:Optional[int]=1, *, container:Optional[CaseConverter]):
        """Gives the specified user in specified guild a case and the case key."""
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
    async def takecase(self, ctx:Context, guild:Optional[Guild], user:Optional[User], amount:Optional[int]=1, *, container:Optional[CaseConverter]):
        """Gives the specified user in specified guild a case and the case key."""
        container: Case()
        if container:
            guild = guild or ctx.guild
            user = user or ctx.author
            amount = amount if amount > 1 else 1
            msg = f"Took **x{abs(amount)} {container}** from **{guild.id or ctx.guild.id}/{user.id or ctx.author}**"
            return await _alter_case(ctx, -amount, container, msg, guild.id, user.id)
        await ctx.send('Specified case could not be found')

    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def ban(self, ctx:Context, guild_id:Optional[int], user_id:Optional[int]):
        """Applies a permanent trade-ban to player in specified guild"""
        player = await Player.get(True, member_id=user_id or ctx.author.id, guild_id=guild_id or ctx.guild.id)
        player.trade_banned = True
        await player.save()
        await ctx.send(f"**{guild_id or ctx.guild.id}/{user_id or ctx.author}** has been trade banned permanently.")

    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def unban(self, ctx:Context, guild_id:Optional[int], user_id:Optional[int]):
        """Removes trade restrictions from a player"""
        player = await Player.get(True, member_id=user_id or ctx.author.id, guild_id=guild_id or ctx.guild.id)
        player.trade_banned = False
        await player.save()
        await ctx.send(f"Removed trade restrictions from **{guild_id or ctx.guild.id}/{user_id or ctx.author}**.")


    @max_concurrency(1, commands.BucketType.default, wait=True)
    @user.command()
    async def delete(self, ctx: Context, guild_id: Optional[int], user_id:Optional[int]):
        """
        Deletes a user from the database
        """
        player = await Player.get(True, member_id=user_id or ctx.author.id, guild_id=guild_id or ctx.guild.id)
        await player.delete()
        await ctx.send(f"**{guild_id or ctx.guild.id}/{user_id or ctx.author.id}** has been deleted from database.")

    @commands.is_owner()
    @user.command()
    async def info(self, ctx, user:Optional[User]):
        user = user or ctx.author
        if user:
            await ctx.send(embed=Embed(
                color = Colour.random()
            ).set_author(name=str(user))\
            .add_field(name='Created at', value=user.created_at)\
            .set_thumbnail(url=user.avatar_url))
        else:
            await ctx.send('User unreachable')

def setup(bot):
    bot.add_cog(UsersCog(bot))
