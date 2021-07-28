from discord import Forbidden
from discord.ext import commands
from discord.ext.commands import (
    CheckFailure, CommandNotFound, NoPrivateMessage, MemberNotFound, BadArgument,
    MissingRequiredArgument, MaxConcurrencyReached, RoleNotFound, CommandOnCooldown
)
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
            Forbidden, RoleNotFound
        }

        embed = Embed(
            title="Command Error:",
            color=Color.RED,
        )

        if isinstance(error, CommandNotFound):
            return
        elif isinstance(error, NoPrivateMessage):
            embed.description = "This command only works inside a server"
        elif isinstance(error, (CheckFailure, BadArgument)):
            embed.description = f"{error.__cause__ or error}"
        elif isinstance(error, Forbidden):
            me = ctx.guild.me
            if ctx.channel.permissions_for(me).send_messages:
                embed.description = ("I cannot perform the action you requested because I'm missing permissions "
                                     "or because my role is too low.")
        else:
            embed.description = str(error)
        try:
            await ctx.send(embed=embed)
        except:
            pass

        if type(error) not in expected:
            raise error


def setup(bot):
    bot.add_cog(ErrorHandlerCog(bot))
