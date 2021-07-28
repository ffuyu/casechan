"""
Core cog contains the main commands of casechan.
casechan's main purpose is to simulate openings
of CS:GO cases and regarding core features are
as follows:

# Opening containers
# Viewing cases/keys
# Viewing inventory
# Viewing balance
"""

import asyncio

from discord.ext.commands.core import max_concurrency
from typing import Optional
from discord.ext import commands
from discord import Member, Embed, Colour
from discord.ext.commands.context import Context
from dpytools import Color

from modules.cases import all_cases
from modules.database import Player, Item
from dpytools.embeds import paginate_to_embeds
from DiscordUtils.Pagination import CustomEmbedPaginator
from modules.cases import open_case
from modules.utils import ItemConverter


def _case(argument:str) -> str:
    for case in all_cases:
        if case.lower() == argument.lower() or case.lower() == '%s case' % argument.lower():
            return case

    return None

def get_key(container:str) -> str:
    return '%s Key' % container


class CoreCog(commands.Cog, name='Core'):
    """
    This category includes the core commands of the bot
    """
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @max_concurrency(number=1, per=commands.BucketType.member, wait=True)
    @commands.command(name='open')
    async def _open(self, ctx:Context, *, container:Optional[_case]):
        """
        Opens a case from your inventory
        """
        if container:
            player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            print(player)
            if container in player.cases and '%s Key' % container in player.keys:
                opening = await open_case(container)
                item = opening[0]
                stats = (opening[1], opening[2])
                player.add_item(item.name, stats)
                player.mod_case(container, -1)
                player.mod_key(get_key(container), -1)
                await player.save()
                # await ctx.send('opening')
                # await asyncio.sleep(5)
                await ctx.send(
                    embed=Embed(
                        description = '**%s**' % item.name,
                        color = item.color
                    ).set_image(url='https://community.akamai.steamstatic.com/economy/image/%s'%item.icon_url).set_footer(text='Float %f | Price: $%.2f' % (stats[0], item.price))
                )
            else:
                await ctx.send('You don\'t have **%s** or its key!' % container)
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
        

    @commands.command()
    async def price(self, ctx, *, query: ItemConverter):
        """
        Shows item info with specified query
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