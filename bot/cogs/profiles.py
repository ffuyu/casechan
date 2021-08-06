from typing import Optional

from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only

from discord import Embed, Colour, Member

from modules.database.players import Player
from modules.database.users import User

from humanize import naturaldate

class ProfilesCog(commands.Cog, name='Profiles'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @commands.command()
    async def profile(self, ctx, user:Optional[User]):
        """Displays a user's public profile"""
        user = user or ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        user_ = await User.get(True, user_id=user.id)
        profile_embed = Embed(description="Registered {} | Voted {} times".format(naturaldate(player.created_at), user_.total_votes), color=Colour.random())
        profile_embed.set_author(name=user)
        profile_embed.set_thumbnail(url=user.avatar_url)
        if user_.acknowledgements:
            profile_embed.add_field(name="Acknowledgements:", value='\n'.join(user_.acknowledgements), inline=True)

        await ctx.send(embed=profile_embed)

def setup(bot):
    bot.add_cog(ProfilesCog(bot))
