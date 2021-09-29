from discord.errors import NotFound
from modules.errors import (
    AlreadyClaimed, BetTooLow, CheatsDisabled, 
    CodeClaimed, CodeExpired, CodeInvalid, 
    ExistingCode, FailedItemGen, ForbiddenAmount, InsufficientBalance, 
    InvalidBet, ItemNotFound, MissingItem, 
    MissingSpace, NotAllowed, RewardsError, TradeNotAllowed, UnableToBuy, 
    UnableToOpen, UnableToSell, ItemNotFound, 
    MissingItem, MissingSpace, TradeNotAllowed,
    MissingCase, MissingKey
)

from colorama import Fore
from bson.errors import InvalidDocument
from discord import Forbidden
from discord.ext import commands
from discord.ext.commands import (
    CheckFailure, CommandNotFound, NoPrivateMessage, MemberNotFound, BadArgument,
    MissingRequiredArgument, MaxConcurrencyReached, RoleNotFound, CommandOnCooldown
)

from discord.ext.commands.errors import BadUnionArgument, BotMissingPermissions, CommandError, MissingPermissions, NotOwner
from dpytools import Embed, Color
from aiohttp.http_exceptions import BadStatusLine

from sqlitedict import SqliteDict

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
            Forbidden, RoleNotFound, BadUnionArgument, BotMissingPermissions, CommandError, MissingItem, 
            ItemNotFound, RewardsError, MissingSpace, InsufficientBalance,
            NotOwner, TradeNotAllowed, CodeExpired, CodeClaimed, CodeInvalid, AlreadyClaimed, ExistingCode,
            InvalidBet, BetTooLow, Forbidden, UnableToBuy, UnableToOpen, UnableToSell, MissingKey, MissingCase, 
            NotFound, BadStatusLine, MissingPermissions, CheatsDisabled, ForbiddenAmount, FailedItemGen,
            NotAllowed
            }
            
        embed = Embed(
            title="Command Error:",
            color=Color.FIRE_ORANGE,
        )

        if isinstance(error, (CommandNotFound)):
            return

        elif isinstance(error, NoPrivateMessage):
            embed.description = "This command only works inside a server"

        elif isinstance(error, (NotOwner)):
            embed.description = 'You are not allowed to use this command!'

        elif isinstance(error, (CheckFailure, BadArgument)):
            embed.description = f"{error.__cause__ or error}"

        elif isinstance(error, Forbidden):
            me = ctx.guild.me
            if ctx.channel.permissions_for(me).send_messages:
                embed.description = ("I cannot perform the action you requested because I'm missing permissions "
                                     "or because my role is too low.")

        elif isinstance(error, BotMissingPermissions):
            embed.description = str(error)

        elif isinstance(error, MaxConcurrencyReached):
            embed.description = f'This command can only be used by {error.number} {str(error.per).split(".")[1]} at same time.'

        elif isinstance(error, CommandOnCooldown):
            embed.description = "Slow down! You can run this command in {:.2f}s".format(error.retry_after)
        else:
            embed.description = str(error)


        if isinstance(error, (InvalidDocument, AttributeError, TypeError, FailedItemGen)):
            print(f'{Fore.RED}COMMAND THAT CAUSED THIS ERROR: {ctx.message.content}{Fore.RESET}')
            embed.description = "Something went wrong! Please [contact us](https://discord.gg/hjH9AQVmyW) if this issue persists."

        if isinstance(error, RewardsError):
            embed.description = str(error)
            embed.set_footer(text='Use the command c.profile to view all the rewards and timers')

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