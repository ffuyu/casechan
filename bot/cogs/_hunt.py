import random
from discord.ext.commands.core import guild_only
from dislash.interactions.message_components import Button, ButtonStyle
from modules.constants import CASE_EMOJI
from discord.colour import Colour
from modules.utils.case_converter import CaseConverter
from typing import Optional
from discord.ext import commands
from modules.cases import Case, Key
from modules.database import Player
from discord import Embed
from dislash import ActionRow

class CaseHuntingCog(commands.Cog, name='CaseHunt'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @commands.command()
    async def casehunt(self, ctx, case:Optional[CaseConverter]):
        case: Case
        if case:
            await ctx.send(case)
            player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            rows = []
            if case.name in player.cases and case.key in player.keys:
                grid_items_x = ['A', 'B', 'C']
                grid_items_y = ['1', '2', '3']
                reward_place = f'{random.choice(grid_items_x)}{random.choice(grid_items_y)}'
                print(reward_place)
                huntEmbed = Embed(
                    title = 'Case Hunt',
                    description = '',
                    color = Colour.random()
                )

                for x in range(grid_items_x):

                    for y in range(grid_items_y): 
                        rows.append(ActionRow(
                            Button(
                                style=ButtonStyle.grey,
                                emoji='❓',
                                custom_id=f'{x}{y}'
                            )
                        ))
                        
                    
                
                await ctx.send('test', components=[])
                

def setup(bot):
    bot.add_cog(CaseHuntingCog(bot))
