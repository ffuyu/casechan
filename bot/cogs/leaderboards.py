from collections import defaultdict
from modules.database import engine
from typing import List, Optional

from discord.ext.commands.core import guild_only
from modules.database.players import Player
from modules.database import Guild as Guild_

from discord.ext import commands, tasks
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.context import Context

from discord import Embed, Colour, Guild

from humanize import ordinal


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
                users_dictionary[f'[{member.name}](https://casechan.com/profile/{user.member_id}/{user.guild_id})'] = await user.inv_total()

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

        leaderboard_embed = Embed(title="World Leaderboard", color=Colour.from_rgb(13, 139, 73))

        if cached_lb:
            leaderboard_embed.description = '\n'.join(
                f"{[*cached_lb][x]}: ${cached_lb[[*cached_lb][x]]:.2f}"
                for x in range(10 if len([*cached_lb]) >= 10 else len([*cached_lb])))
            
            leaderboard_embed.set_footer(text='Based on inventory worth, not wallets.')

            # running_guild = await Guild_.get(True, guild_id=ctx.guild.id)

            # if len(cached_lb) >= 10:
            #     if not running_guild.is_excluded and not ctx.guild.id in cached_lb[10:]: 
            #         leaderboard_embed.footer(text=leaderboard_embed.footer.text+f'\nYour server is {ordinal(list(cached_lb.values()).index(ctx.guild.id))}')


        else: leaderboard_embed.description = 'Loading...'

        await ctx.send(embed=leaderboard_embed)
        
    @tasks.loop(minutes=10)
    async def update_cached_lb(self):
        global cached_lb
        players = await engine.find(Player)
        guilds = defaultdict(float)

        def filter(text:str)->str:
            chars = ['*', '|', '~', '>', '<', '`', '[', ']', '(', ')']
            phrases = ['discord.gg', 'discord.com', 'https://', 'http://', 'www.']
            for c in chars: text = text.replace(c, '')
            for p in phrases: text = text.replace(p, '')
            return text

        for player in players:
            if player.guild_id in [g.id for g in self.bot.guilds]:
                guild = await Guild_.get(True, guild_id=player.guild_id)
                if guild.excluded_from_leaderboards or guild.server_cheats_enabled: continue
                guilds[filter(self.bot.get_guild(player.guild_id).name)]+=await player.inv_total()
                
        if guilds.get('fuyu\'s development server', None): guilds['**[casechan support server](https://casechan.com/discord)**'] = guilds.pop('fuyu\'s development server')
        
        cached_lb = dict(sorted(guilds.items(), key=lambda item: item[1], reverse=True))

def setup(bot):
    bot.add_cog(LeaderboardsCog(bot))
