from modules.database.players import Player
from discord.ext import commands
from discord import Member, Embed, Colour

from typing import Optional

from datetime import datetime

from modules.database import Trade

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
            return await ctx.send("Please specify a user to create a trade offer")
        
        sender = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        receiver = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)

        offer = await Trade.get(True, sender=sender.doc(), receiver=receiver.doc(), created_at=datetime.now())
        await offer.save()
        embed = Embed(
            description = 
            f"""
            **Trade offer created. Please follow the instructions to manage:**\n
            - [Login](https://casechan.com/login) to casechan.com
            - Follow [this link](https://casechan.com/trades/{offer.id})
            """,
            color = Colour.blue()
        ).set_footer(text=f"Trade ID: {offer.id}")

        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(Trading(bot))
