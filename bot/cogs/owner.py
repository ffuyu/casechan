from modules.database.players import Player
from modules.database.users import UserData
from typing import Optional
from discord import Embed, Guild
from discord.abc import User
from discord.activity import Game
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import max_concurrency
from dpytools import Color
from dpytools.checks import only_these_users

from modules.config import OWNERS_IDS
from modules.utils import update_item_database
from modules.database import Guild as Guild_
from dislash import *

class OwnerCog(commands.Cog, name='owner'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.is_owner()
    @only_these_users(*OWNERS_IDS)
    @commands.group(hidden=True)
    async def owner(self, ctx: Context):
        pass

    @max_concurrency(1, BucketType.default, wait=False)
    @owner.command(name='update-items', hidden=True)
    async def _update_items(self, ctx: Context):
        """Updates the item's database"""
        msg = await ctx.send(embed=Embed(
            description=f"Updating Item's Database...",
            color=Color.YELLOW
        ))
        await update_item_database()
        await msg.edit(embed=Embed(
            description='Done, items updated!',
            color=Color.LIME,
        ), delete_after=60.0)

    @owner.command()
    async def status(self, ctx: Context, *, name: str):
        await self.bot.change_presence(activity=Game(name=name))

    @owner.command()
    async def svinfo(self, ctx, *, guild:Optional[Guild]):
        guild = guild or ctx.guild
        g = await Guild_.get(True, guild_id=guild.id)
        await g.save()
        embed = Embed(
            title = guild,
            description = f'```json{g.doc()}```'
        )
        embed.set_footer(text=guild.id)
        row = ActionRow(
            Button(style=ButtonStyle.link, url=f'https://casechan.com/admin/bot/botguildconfig/{g.id}', label="Edit")
        )
        await ctx.send(embed=embed, components=[row])

    @owner.command()
    async def uinfo(self, ctx, user:Optional[User], guild:Optional[Guild]):
        user = user or ctx.author
        guild = guild or ctx.guild
        if user:
            player = await Player.get(member_id=user.id, guild_id=guild.id)
            userdata = await UserData.get(True, user_id=user.id)
            await userdata.save()

            embed = Embed(
                title = user,
                description = f'```json{userdata.doc()}```'
            )
            embed.set_footer(text=user.id)
            row = ActionRow(
                Button(style=ButtonStyle.link, url=f'https://casechan.com/admin/bot/botplayer/{player.id}', label="Edit Player", disabled=not player),
                Button(style=ButtonStyle.link, url=f'https://casechan.com/admin/bot/botuser/{userdata.id}', label="Edit User")
            )
            await ctx.send(embed=embed, components=[row])
        else: await ctx.send('User unreachable')

def setup(bot):
    bot.add_cog(OwnerCog(bot))
