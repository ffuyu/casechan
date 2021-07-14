"""
Core cog contains the main commands of casechan.
casechan's main purpose is to simulate openings
of CS:GO cases and regarding core features are
as follows:

# Opening containers
# Viewing cases/keys
# Viewing inventory
# Viewing balance
"""

from typing import Optional
from discord.ext import commands
from discord import Member, Embed, Colour
from discord.ext.commands.context import Context
from modules.cases import all_cases
from modules.database import Player


def case(argument:str) -> str:
    for case in all_cases:
        if case.lower() == argument.lower() or case.lower() == '{} case'.format(argument.lower()):
            return case

    return None

class Cog(commands.Cog, name='Core'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.command()
    async def open(self, ctx:Context, *, container:Optional[case]):
        if container:
            pass # open case

        return await ctx.send('Invalid case specified')

    @commands.command()
    async def cases(self, ctx:Context, user:Optional[Member]):
        user = user or ctx.author
        player = Player(member_id=user.id, guild_id=ctx.guild.id)
        if player.cases:
            return await ctx.send(embed=Embed(
                title = '%s\'s Cases' % user,
                description = '\n'.join(player.cases),
                color = Colour.random()
            ))
        return await ctx.send('**%s** has no cases to display' % user) # FIXME (replace with an embed)

def setup(bot):
    bot.add_cog(Cog(bot))