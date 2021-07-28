from discord.ext import commands
from discord import Member
from typing import Optional

class Trading(commands.Cog, name='Trading'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.command()
    async def trade(self, ctx, user:Optional[Member]):
        """Create a trade offer with the specified user"""
        if not user:
            return await ctx.send("Please specify a user to trade with")
        
        # create trade

        
def setup(bot):
    bot.add_cog(Trading(bot))
