from modules.database import engine
from typing import Optional

from discord.ext.commands.core import guild_only
from modules.database.players import Player

from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.context import Context

from discord import Embed, Colour, Guild


class LeaderboardsCog(commands.Cog, name='Leaderboards'):
    """Contains the leaderboard commands"""
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')


    @guild_only()
    @commands.cooldown(10, 30, BucketType.guild)
    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx: Context, *, guild: Optional[Guild]):
        """View the inventory worth leaderboard for the server"""
        guild = guild or ctx.guild
        users = await engine.find(Player, Player.guild_id==guild.id)
        users_dictionary = {}
        for user in users:
            member = guild.get_member(user.member_id)
            if member:
                users_dictionary[member.name] = await user.inv_total()

        leaderboard = sorted(users_dictionary.items(), key=lambda item: item[1], reverse=True)
        await ctx.send(
            embed=Embed(
                description='\n'.join(f"**{k}**: ${v:.2f}" for k, v in leaderboard[:10]),
                color=Colour.random()
            ).set_footer(text="Based on inventory worth | Total server inventory worth: ${:.2f}\nUse the command 'top' to view the world leaderboard.".format(
                sum([x for x in users_dictionary.values()]))).set_author(name=guild, icon_url=guild.icon_url)
        )

    @commands.cooldown(10, 60, BucketType.member)
    @commands.command()
    async def top(self, ctx):
        """Lists the top 10 most rich servers based on inventory worth"""
        guilds_dictionary = {}
        for guild in self.bot.guilds:
            users = await Player.find(guild_id=guild.id)
            guilds_dictionary[guild.name] = sum([await x.inv_total() for x in users])

        leaderboard = dict(sorted(guilds_dictionary.items(), key=lambda item: item[1], reverse=True))

        embed = Embed(
            title="TOP 10 SERVERS",
            description='\n'.join(
                "**{}**: ${:.2f}".format(list(leaderboard.keys())[x], leaderboard[list(leaderboard.keys())[x]]) for x in
                range(10 if len(list(leaderboard.keys())) >= 10 else len(list(leaderboard.keys())))),
            color=Colour.from_rgb(252, 194, 3)
        ).set_footer(text='Based on inventory worth, not wallets.').set_thumbnail(
            url="https://img.icons8.com/color-glass/48/000000/star.png")

        await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(LeaderboardsCog(bot))
