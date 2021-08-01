from discord import Member
from modules.database.players import Player
from typing import Optional
from modules.utils.case_converter import CaseConverter
from discord.ext import commands
from discord.ext.commands.core import guild_only
from discord.ext.commands.context import Context
from modules.cases import Case

class BattlesCog(commands.Cog, name='Case Battles'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @commands.command(aliases=['casebattle', 'cb'])
    async def battle(self, ctx:Context, user:Optional[Member], case:Optional[CaseConverter]):
        case: Case
        if case and user:
            await ctx.send(case)
            player_1 = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            player_2 = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
            if case.name in player_1.cases and case.key in player_1.keys:
                if case.name in player_2.cases and case.key in player_2.keys:
                    pass


def setup(bot):
    bot.add_cog(BattlesCog(bot))
