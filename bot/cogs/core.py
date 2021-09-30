"""
Core cog contains the main commands of casechan.
casechan's main purpose is to simulate openings
of CS:GO cases and regarding core features are
as follows:

# Opening containers
# Viewing list of owned cases
# Viewing list of owned keys
# Viewing inventory
# Viewing balance
"""
import asyncio
import time
import logging

from sqlitedict import SqliteDict
from shortuuid import ShortUUID
from modules.database.guilds import Guild
from collections import defaultdict

from modules.utils.paginate import dict_paginator
from modules.utils.checks import able_to_opencontainer, emojify
from modules.database.items import Item, sort_items
from modules.database.players import Player
from modules.cases import Capsule, Case, Container, Key, Package
from modules.database import Player, SafePlayer
from modules.database.users import UserData
from modules.utils.case_converter import ContainerConverter
from modules.utils import Timer

from etc.emojis import emojis

from typing import Optional

from DiscordUtils.Pagination import CustomEmbedPaginator
from discord import Member, Colour, PartialEmoji
from discord.ext import commands, tasks
from discord.ext.commands.context import Context
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle
from dpytools.embeds import Embed
from dpytools.embeds import paginate_to_embeds

allowed_characters = "ABCDEFGHJKLMNPRSTUVXYZ23456789"
uuid_gen = ShortUUID()
log = logging.getLogger(__name__)
last_opening_durations = []
cases_opened = 0
uuid_gen.set_alphabet(''.join(list(allowed_characters)))


def disable_row(row: ActionRow) -> ActionRow:
    for button in row.buttons:
        button.disabled = True

    return row
 

def results_row(player: Player, amount: int):
    row = ActionRow(
        Button(style=ButtonStyle.grey,
               label="Claim" if amount == 1 else "Claim all",
               custom_id="claim",
               emoji=PartialEmoji(name='📥')),
        Button(style=ButtonStyle.green,
               label="Sell" if amount == 1 else "Sell all",
               custom_id="sell",
               emoji=PartialEmoji(name='💸'),
               disabled=player.trade_banned),
        Button(style=ButtonStyle.grey,
               label=f"{player.inv_items_count}/{player.inventory_limit}",
               custom_id="invsize",
               disabled=True)
    )

    return row


class CoreCog(commands.Cog, name='Core'):
    """
    This category includes the core commands of the bot
    """

    def __init__(self, bot):
        self.bot = bot
        self.log_stats.start()
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @max_concurrency(number=1, per=commands.BucketType.member, wait=True)
    @commands.command(name='open')
    async def _open(self, ctx: Context, amount: Optional[int] = 1, *, container: Optional[ContainerConverter]):
        """
        Opens a case from your cases
        """
        if not container and not isinstance(container, Key):
            return await ctx.send('Not a valid case name!')

        async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
            amount = amount if amount > 0 else 1
            if able_to_opencontainer(player, container, amount):

                user = await UserData.get(True, user_id=ctx.author.id)
                multiplier = user.multiplier
                sleep_duration = 6.0 / multiplier

                opening_embed = Embed(
                    description=emojify(ctx, f'**<a:casechanloading:874960632187879465> {container}**'),
                    color=Colour.random(),
                    image=container.asset
                )

                opening_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

                message = await ctx.reply(embed=opening_embed)

                # Opening cases

                start = time.perf_counter()
                try: 
                    items = [await player.open_case(container) for _ in range(amount)]
                except:
                    await message.delete()
                    return
                stop = time.perf_counter()
            
                last_opening_durations.append(stop-start)
                global cases_opened
                cases_opened += 1
                item_objects = sort_items([k for k, *_ in items])

                await asyncio.sleep(max(sleep_duration - (stop-start), 0))

                # Displaying results based on amount
                if amount > 1:
                    results = Embed(
                        color=Colour.random()
                    )
                    results.description = f'You have opened {amount}x {container.name} and received **${sum([x.price for x in item_objects]):.2f}** worth of items'

                    results.add_field(name='Items:', value=emojify(ctx, '\n'.join([f'{emojis.get(x.rarity)} **{x.name}** ${x.price}' for i, x in enumerate(
                        item_objects) if i < 5]) + (f'\n\n*({amount-5} more items)*' if len(item_objects) > 5 else '')))

                else:
                    item, *stats = items[0]
                    results = Embed(
                        description=emojify(
                            ctx, f'{emojis.get(item.rarity)} **{item.name}**'),
                        color=item.color,
                        image=f'https://community.akamai.steamstatic.com/economy/image/{item.icon_url}'
                    ).set_footer(text='Float %f | Paint Seed: %d | Price: $%.2f' % (stats[0], stats[1], item.price)) \
                        .set_author(name=container, icon_url=container.asset)

                results.set_author(name=container.name, icon_url=container.asset)
                row = results_row(player, amount)
                await message.delete()
                message = await ctx.send(
                    content=None,
                    embed=results,
                    mention_author=False,
                    components=[row],
                )

                def check(inter_): return inter_.author == ctx.author

                try:
                    inter = await message.wait_for_button_click(check=check, timeout=30)
                except asyncio.TimeoutError:
                    await message.edit(components=[disable_row(row)])
                    if amount != 1:
                        for item in items:
                            i, *s = item
                            player.add_item(i.name, s)
                    else:
                        player.add_item(item.name, stats)
                else:
                    await message.edit(components=[disable_row(row)])
                    if inter.clicked_button.custom_id == 'claim':
                        if amount != 1:
                            for item in items:
                                i, *s = item
                                player.add_item(i.name, s)
                            await inter.reply(f'Claimed **{len(item_objects)}** items', ephemeral=True)
                        else:
                            player.add_item(item.name, stats)
                            await inter.reply(f'Claimed **{item.name}**', ephemeral=True)

                    elif inter.clicked_button.custom_id == 'sell':
                        fees = user.fees
                        total_received = 0.0
                        if amount != 1:
                            for item in item_objects:
                                total_received += (item.price * fees)

                        else:
                            total_received += (item.price * fees)

                        await inter.send(
                            content=f'You\'ve received **${total_received:.2f}**',
                            ephemeral=True
                        )

                        player.balance += total_received
                finally:
                    await player.save()
                    

    @commands.cooldown(10, 60, BucketType.member)
    @commands.command()
    async def cases(self, ctx: Context, *, user: Optional[Member]):
        """List the cases you currently have."""
        user = user if user and not user.bot else ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)

        if player.cases:
            return await dict_paginator(f'{user}\'s Cases', ctx, player.cases)

        await ctx.send(f'**{user}** has no cases to display')

    @commands.cooldown(10, 60, BucketType.member)
    @commands.command()
    async def packages(self, ctx: Context, *, user: Optional[Member]):
        """List the packages you currently have."""
        user = user if user and not user.bot else ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)

        if player.packages:
            return await dict_paginator(f'{user}\'s Packages', ctx, player.packages)

        await ctx.send(f'**{user}** has no packages to display')

    @commands.cooldown(10, 60, BucketType.member)
    @commands.command()
    async def capsules(self, ctx: Context, *, user: Optional[Member]):
        """List the capsules you currently have."""
        user = user if user and not user.bot else ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)

        if player.capsules:
            return await dict_paginator(f'{user}\'s Capsules', ctx, player.capsules)

        await ctx.send(f'**{user}** has no capsules to display')

    @commands.cooldown(10, 60, BucketType.member)
    @commands.command()
    async def keys(self, ctx: Context, *, user: Optional[Member]):
        """List the cases you currently have."""
        user = user if user and not user.bot else ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)

        if player.keys:
            return await dict_paginator(f'{user}\'s Keys', ctx, player.keys)

        await ctx.send(f'**{user}** has no keys to display')

    @commands.cooldown(10, 30, BucketType.member)
    @commands.command(aliases=['inv'])
    async def inventory(self, ctx: Context, *, user: Optional[Member]):
        """View your inventory"""
        user = user if user and not user.bot else ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        guild = await Guild.get(True, guild_id=ctx.guild.id)

        if player.inventory:
            # sort items by price
            sorted_inventory = sort_items(await player.inv_items())
            # create a blank items text
            items_text = ''
            # append items to items text
            for item in sorted_inventory:
                items_text += f'**{player.item_count(item.name)}** {item.name} \n'
            # create pages from items text
            pages = paginate_to_embeds(
                description=items_text, title=f'{user}\'s Inventory', max_size=400, color=Colour.random())
            # create paginator from pages
            paginator = CustomEmbedPaginator(
                ctx, remove_reactions=True, timeout=20)
            # add arrows if there are multiple pages
            if len(pages) > 1:
                paginator.add_reaction(
                    '⬅️', "back"), paginator.add_reaction('➡️', "next")
            # run the paginator
            message = await paginator.run(pages)
            # if guild excluded from the website, return
            # otherwise, show 'View at casechan.com' button
            if guild.excluded_from_web:
                return

            else:
                return await message.edit(
                    components=[ActionRow(Button(
                        style=ButtonStyle.link,
                        label='View at casechan.com',
                        url=f'https://casechan.com/profiles/{ctx.author.id}/{ctx.guild.id}#inventory'
                    )
                    )]
                )
        await ctx.reply(f'**{user}** has no items to display')

    @guild_only()
    @commands.cooldown(10, 30, BucketType.member)
    @commands.command(aliases=["bal", "b", "networth", "nw"])
    async def balance(self, ctx, *, user: Optional[Member]):
        """Displays your wallet, inventory and net worth all at once"""
        user = user if user and not user.bot else ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        guild = await Guild.get(True, guild_id=ctx.guild.id)

        inv_total = await player.inv_total()
        net_worth = player.balance + inv_total

        embed = Embed(color=Colour.random()).set_author(
            name=user, icon_url=user.avatar_url)
        embed.add_fields(inline=True, **{
            'Wallet':    f'${player.balance:.2f}',
            'Inventory': f'${inv_total:.2f}',
            'Net worth': f'${net_worth:.2f}',
        })
        if not guild.excluded_from_web:
            embed.set_footer(text="casechan.com/profile")

        await ctx.send(embed=embed)

    @tasks.loop(minutes=10)
    async def log_stats(self):
        global last_opening_durations
        global cases_opened
        if last_opening_durations: print(f'Average case opening duration in the last 10 minutes: {sum(last_opening_durations)/len(last_opening_durations):.6f}')
            
        if cases_opened: print(f'{cases_opened} cases opened in the last 10 minutes,')
            
        last_opening_durations = []
        cases_opened = 0
            

    @log_stats.before_loop
    async def before_log_stats(self):
        # start logging after 60 seconds after bot is ready
        await self.bot.wait_until_ready()
        await asyncio.sleep(10)
        


def setup(bot):
    bot.add_cog(CoreCog(bot))
