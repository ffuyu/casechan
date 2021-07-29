"""
Core cog contains the main commands of casechan.
casechan's main purpose is to simulate openings
of CS:GO cases and regarding core features are
as follows:

# Opening containers
# Viewing cases/keys
# Viewing inventory
# Viewing balance
# Viewing leaderboards
"""

import asyncio
from os import name

from discord.ext.commands.core import guild_only, max_concurrency
from typing import Optional
from discord.ext import commands
from discord import Member, Embed, Colour
from discord.ext.commands.context import Context
from dpytools import Color

from modules.cases import all_cases
from modules.database import Player, Item, engine, GuildConfig
from dpytools.embeds import paginate_to_embeds
from DiscordUtils.Pagination import CustomEmbedPaginator
from modules.cases import open_case, Case
from modules.utils import ItemConverter

def _case(argument:str) -> str:
    for case in all_cases:
        if case.lower() == argument.lower() or case.lower() == '%s case' % argument.lower():
            return Case(case)

    return None

class CoreCog(commands.Cog, name='Core'):
    """
    This category includes the core commands of the bot
    """
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @max_concurrency(number=1, per=commands.BucketType.member, wait=True)
    @commands.command(name='open')
    async def _open(self, ctx:Context, *, container:Optional[_case]):
        """
        Opens a case from your inventory
        """
        if container:
            player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            if container.name in player.cases and container.key in player.keys:
                # Opening animation
                opening_embed = Embed(
                    description = container
                ).set_image(url=container.asset)
            
                message = await ctx.send(embed=opening_embed, reference=ctx.message)
                await asyncio.sleep(5)
                # Displaying results

                item, *stats = await container.open()
                player.add_item(item.name, stats)
                player.mod_case(container.name, -1)
                player.mod_key(container.key, -1)
                await player.save()
                
                return await message.edit(
                    embed=Embed(
                        description = '**{}**'.format(item.name),
                        color = item.color
                    ).set_image(url='https://community.akamai.steamstatic.com/economy/image/{}'.format(item.icon_url))\
                     .set_footer(text='Float %f | Paint Seed: %d | Price: $%.2f' % (stats[0], stats[1], item.price))\
                     .set_author(name=container, icon_url=container.asset)
                )
            else:
                return await ctx.send('You don\'t have **%s** or its key!' % container)
        else:
            return await ctx.send('Not a valid case name!')

    @commands.command(aliases=['keys'])
    async def cases(self, ctx:Context, user:Optional[Member]):
        user = user or ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        
        if ctx.invoked_with == 'cases':
            if player.cases:
                return await ctx.send(embed=Embed(
                    title = '{}\'s Cases'.format(user),
                    description = '\n'.join(f'{v}x {k}' for k,v in player.cases.items())
,
                    color = Colour.random()
                ))

            return await ctx.send(f'**{user}** has no cases to display') # FIXME (replace with an embed)

        elif ctx.invoked_with == 'keys':
            if player.keys:
                return await ctx.send(embed=Embed(
                    title = '{}\'s Keys'.format(user),
                    description = '\n'.join(f'{v}x {k}' for k,v in player.keys.items()),
                    color = Colour.random()
                ))

            return await ctx.send(f'**{user}** has no keys to display') # FIXME (replace with an embed)


    @commands.command(aliases=['inv'])
    async def inventory(self, ctx:Context, user:Optional[Member]):
        user = user or ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        inv_items = await player.inv_items()
        if inv_items:
            pages = paginate_to_embeds(description='\n'.join([item.name for item in inv_items]), title='{}\'s Inventory'.format(user), max_size=400, color=Colour.random())
            paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")

            return await paginator.run(pages)
        return await ctx.reply('**{}** has no items to display'.format(user))
        
    @guild_only()
    @commands.command(aliases=["bal", "b"])
    async def balance(self, ctx, user:Optional[Member]):
        user = user or ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        inv_total = await player.inv_total()
        await ctx.send(
            embed=Embed(
                color = Colour.random()
            ).set_author(name=ctx.author, icon_url=ctx.author.avatar_url)\
             .add_field(name="Wallet", value='${:.2f}'.format(player.balance), inline=True)
             .add_field(name="Inventory", value='${:.2f}'.format(inv_total), inline=True)
             .add_field(name="Net worth", value='${:.2f}'.format(player.balance+inv_total), inline=True)
        )
        
    @guild_only()
    @commands.command()
    async def leaderboard(self, ctx:Context):
        """View the inventory worth leaderboard for the server"""
        users = await engine.find(Player, Player.guild_id == ctx.guild.id)
        users_dictionary = {}
        for user in users:
            member = ctx.guild.get_member(user.member_id)
            if member:
                users_dictionary[member] = await user.inv_total()

        leaderboard = dict(sorted(users_dictionary.items(), key=lambda item: item[1], reverse=True))
        
        await ctx.send(
            embed=Embed(
                description = '\n'.join("{}: {:.2f}".format(list(leaderboard.keys())[x], leaderboard[list(leaderboard.keys())[x]]) for x in range(10 if len(list(leaderboard.keys())) >= 10 else len(list(leaderboard.keys())))),
                color = Colour.random()
            ).set_footer(text="Based on inventory worth | Total server inventory worth: ${:.2f}".format(sum([x for x in users_dictionary.values()]))).set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        )

    @commands.command()
    async def top(self, ctx):
        """Lists the top 10 most rich servers based on inventory worth"""
        guilds_dictionary = {}
        all_guilds = await engine.find(GuildConfig)
        for guild in all_guilds:
            users = await engine.find(Player, Player.guild_id == guild.guild_id)
            guild_object = self.bot.get_guild(guild.guild_id)
            guilds_dictionary[guild_object.name] = sum([await x.inv_total() for x in users])

        leaderboard = dict(sorted(guilds_dictionary.items(), key=lambda item: item[1], reverse=True))
        
        embed = Embed(
            title = "TOP 10 SERVERS",
            description = '\n'.join("{}: ${:.2f}".format(list(leaderboard.keys())[x], leaderboard[list(leaderboard.keys())[x]]) for x in range(10 if len(list(leaderboard.keys())) >= 10 else len(list(leaderboard.keys())))),
            color = Colour.from_rgb(252, 194, 3)
        ).set_thumbnail(url="https://img.icons8.com/color-glass/48/000000/star.png")
        
        await ctx.send(embed=embed)

        



    @commands.command()
    async def price(self, ctx, *, query: ItemConverter):
        """
        Shows item price with specified query
        Args:
            query: the name of the item to search
        """
        if query:
            query: Item
            await ctx.send(embed=query.to_embed(minimal=True))
        else:
            await ctx.send(embed=Embed(description='Item not found', color=Color.RED))

    @commands.command()
    async def inspect(self, ctx, *, query: ItemConverter):
        """
        Shows item price and asset with specified query
        Args:
            query: the name of the item to search
        """
        if query:
            query: Item
            await ctx.send(embed=query.to_embed())
        else:
            await ctx.send(embed=Embed(description='Item not found', color=Color.RED))


def setup(bot):
    bot.add_cog(CoreCog(bot))