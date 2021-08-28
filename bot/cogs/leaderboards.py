from modules.database import engine
from typing import Optional

from discord.ext.commands.core import guild_only
from modules.database.players import Player

from discord.ext import commands, tasks
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.context import Context

from discord import Embed, Colour, Guild

cached_lb = None

class LeaderboardsCog(commands.Cog, name='Leaderboards'):
    """Contains the leaderboard commands"""
    def __init__(self, bot):
        self.bot = bot
        self.update_cached_lb.start()
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
            if member and not user.trade_banned:
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
        global cached_lb

        if not cached_lb:
            guilds_dictionary = {} 
            for guild in self.bot.guilds:
                users = await engine.find(Player, Player.guild_id==guild.id)
                guilds_dictionary[guild.name] = sum([await x.inv_total() for x in users if not x.trade_banned])

            cached_lb = dict(sorted(guilds_dictionary.items(), key=lambda item: item[1], reverse=True))

        embed = Embed(
            title="World Leaderboard",
            description='\n'.join(
                f"**{[*cached_lb][x]}**: ${cached_lb[[*cached_lb][x]]:.2f}"
                for x in range(10 if len([*cached_lb]) >= 10 else len([*cached_lb]))),
            color=Colour.from_rgb(13, 139, 73)
        )
        
        embed.set_footer(text='Based on inventory worth, not wallets.')
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/877878954424406016.png?v=1")
        await ctx.send(embed=embed)
        
    @tasks.loop(minutes=10)
    async def update_cached_lb(self):
        global cached_lb
        guilds_dictionary = {} 
        
        for guild in self.bot.guilds:
            users = await engine.find(Player, Player.guild_id==guild.id)
            guilds_dictionary[guild.name] = sum([await x.inv_total() for x in users if not x.trade_banned])

        cached_lb = dict(sorted(guilds_dictionary.items(), key=lambda item: item[1], reverse=True))

def setup(bot):
    bot.add_cog(LeaderboardsCog(bot))
