from datetime import datetime
from typing import Optional

from discord.ext import commands
from discord.ext.commands.core import guild_only, is_owner

from discord import Embed, Colour, User

from modules.database.players import Player
from modules.database.users import UserData
from modules.database import engine

from humanize import naturaldate
from humanize.time import naturaltime

class ProfilesCog(commands.Cog, name='Profiles'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @commands.command(hidden=True)
    async def profile(self, ctx, user:Optional[User]):
        """Displays a user's public profile"""
        user = user if user and not user.bot else ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        userdata = await UserData.get(True, user_id=user.id)
        profile_embed = Embed(color=Colour.random())
        profile_embed.add_field(name=f'Selling fees:', value=f'{"5" if userdata.is_boosted else "15"}%', inline=True)
        profile_embed.add_field(name=f'Total votes:', value=f'{userdata.total_votes}', inline=True)
        profile_embed.set_author(name=user)
        profile_embed.set_thumbnail(url=user.avatar_url)
        profile_embed.set_footer(text=player.id)
        profile_embed.add_field(name=ctx.guild, value=
        f'''
        Hourly: {'**READY**' if player.hourly_available else f'<t:{int((player.hourly_remaining.timestamp()))}:R>'}
        Daily: {'**READY**' if player.daily_available else f'<t:{int((player.daily_remaining.timestamp()))}:R>'}
        Weekly: {'**READY**' if player.weekly_available else f'<t:{int((player.weekly_remaining.timestamp()))}:R>'}
        ''', inline=False)
        if userdata.acknowledgements:
            profile_embed.add_field(name="Acknowledgements:", value='\n'.join(userdata.acknowledgements), inline=False)

        await ctx.send(embed=profile_embed)

    @is_owner()
    @commands.group(aliases=["ack"], hidden=True)
    async def acknowledgement(self, ctx):
        pass

    @acknowledgement.command(aliases=["a"])
    async def add(self, ctx, user:Optional[User], *, acknowledgement:str):
        user = user if user and not user.bot else ctx.author
        u = await UserData.get(True, user_id=user.id)
        u.acknowledgements.append(acknowledgement)
        await u.save()
        await ctx.send(f"Added {acknowledgement} to {user}")

    @acknowledgement.command(aliases=["r"])
    async def remove(self, ctx, user:Optional[User], *, acknowledgement:str):
        user = user if user and not user.bot else ctx.author
        u = await UserData.get(True, user_id=user.id)
        u.acknowledgements.remove(acknowledgement)
        await u.save()
        await ctx.send(f"Removed {acknowledgement} from {user}")

    @acknowledgement.command(aliases=["clr"])
    async def clear(self, ctx, user:Optional[User]):
        user = user if user and not user.bot else ctx.author
        u = await UserData.get(True, user_id=user.id)
        u.acknowledgements.clear()
        await u.save()
        await ctx.send(f"Removed all acknowledgements from {user}")

def setup(bot):
    bot.add_cog(ProfilesCog(bot))
