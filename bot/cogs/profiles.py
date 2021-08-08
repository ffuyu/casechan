from typing import Optional

from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, is_owner

from discord import Embed, Colour, Member, User
from humanize.time import naturaltime

from modules.database.players import Player
from modules.database.users import UserData

from humanize import naturaldate

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
        profile_embed = Embed(description="Registered {} | Voted {} times\nSelling fees: {}".format(naturaldate(player.created_at), userdata.total_votes, f'**5%** | Valid for {naturaltime(userdata.vote_expiration)}' if userdata.is_boosted else '15% | [Vote now](https://top.gg/bot/864925623826120714/vote) for 5%'), color=Colour.random())
        profile_embed.set_author(name=user)
        profile_embed.set_thumbnail(url=user.avatar_url)
        if userdata.acknowledgements:
            profile_embed.add_field(name="Acknowledgements:", value='\n'.join(userdata.acknowledgements), inline=True)

        await ctx.send(embed=profile_embed)

    @is_owner()
    @commands.group(aliases=["ack"], hidden=True)
    async def acknowledgement(self, ctx):
        pass

    @acknowledgement.command(aliases=["a"])
    async def add(self, ctx, user:Optional[User], *, acknowledgement:str):
        user = user or ctx.author
        u = await UserData.get(True, user_id=user.id)
        u.acknowledgements.append(acknowledgement)
        await u.save()
        await ctx.send(f"Added {acknowledgement} to {user}")

    @acknowledgement.command(aliases=["r"])
    async def remove(self, ctx, user:Optional[User], *, acknowledgement:str):
        user = user or ctx.author
        u = await UserData.get(True, user_id=user.id)
        u.acknowledgements.remove(acknowledgement)
        await u.save()
        await ctx.send(f"Removed {acknowledgement} from {user}")

    @acknowledgement.command(aliases=["clr"])
    async def clear(self, ctx, user:Optional[User]):
        user = user or ctx.author
        u = await UserData.get(True, user_id=user.id)
        u.acknowledgements.clear()
        await u.save()
        await ctx.send(f"Removed all acknowledgements from {user}")

def setup(bot):
    bot.add_cog(ProfilesCog(bot))
