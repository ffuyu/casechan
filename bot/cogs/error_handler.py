from copy import Error
from modules.errors import DailyError, HourlyError, InsufficientBalance, ItemNotFound, MissingCase, MissingItem, MissingKey, MissingSpace, NotMarketable, WeeklyError
from discord import Forbidden
from discord.ext import commands
from discord.ext.commands import (
    CheckFailure, CommandNotFound, NoPrivateMessage, MemberNotFound, BadArgument,
    MissingRequiredArgument, MaxConcurrencyReached, RoleNotFound, CommandOnCooldown
)
from discord.ext.commands.errors import BadUnionArgument, BotMissingPermissions, CommandError, NotOwner
from dpytools import Embed, Color

class ErrorHandlerCog(commands.Cog, name='Error Handler'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.Cog.listener('on_command_error')
    async def except_cmd_error(self, ctx, error):
        expected = {
            CheckFailure, CommandNotFound, NoPrivateMessage, MemberNotFound,
            BadArgument, MissingRequiredArgument, MaxConcurrencyReached, CommandOnCooldown,
            Forbidden, RoleNotFound, BadUnionArgument, BotMissingPermissions, CommandError, 
            MissingItem, NotMarketable, ItemNotFound, DailyError, HourlyError, WeeklyError,
            MissingSpace, MissingCase, MissingKey, InsufficientBalance
            }
        embed = Embed(
            title="Command Error:",
            color=Color.RED,
        )

        if isinstance(error, (CommandNotFound)):
            return
        elif isinstance(error, NoPrivateMessage):
            embed.description = "This command only works inside a server"
        elif isinstance(error, (CheckFailure, BadArgument)):
            embed.description = f"{error.__cause__ or error}"
            print(error.__cause__ or error)
        elif isinstance(error, Forbidden):
            me = ctx.guild.me
            if ctx.channel.permissions_for(me).send_messages:
                embed.description = ("I cannot perform the action you requested because I'm missing permissions "
                                     "or because my role is too low.")
        elif isinstance(error, BotMissingPermissions):
            embed.description = str(error)
        elif isinstance(error, NotOwner):
            embed.description = 'You are not allowed to use this command!'
        elif isinstance(error, MaxConcurrencyReached):
            embed.description = f'This command can only be used by {error.number} {error.per} at same time.'
        else:
            embed.description = str(error)
        try:
            await ctx.send(embed=embed)
        except:
            me = ctx.guild.me
            if ctx.channel.permissions_for(me).send_messages:
                await ctx.send(embed.description)

        if type(error) not in expected:
            raise error


def setup(bot):
    bot.add_cog(ErrorHandlerCog(bot))
