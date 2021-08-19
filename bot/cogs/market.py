import asyncio, random
from DiscordUtils.Pagination import CustomEmbedPaginator

from discord.embeds import Embed
from discord import Colour

from discord.ext.commands.context import Context
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency

from dislash.interactions.message_components import ActionRow, Button

from dpytools import Color

from typing import Optional, Union

from dpytools.embeds import paginate_to_embeds

from modules.utils.checks import able_to_buy, able_to_sell
from modules.constants import ButtonTypes
from modules.cases import Case, Key, all_cases
from modules.database.items import Item, generate_stats
from modules.database.players import SafePlayer
from modules.utils.case_converter import CaseConverter
from modules.utils.item_converter import ItemConverter
from modules.utils.operator_converter import OperatorConverter

case_prices = {}

async def sell_prompt(ctx):
    row = ActionRow(
        Button(
            style=ButtonTypes.CONFIRM,
            label="Confirm",
            custom_id="confirm"),
        Button(
            style=ButtonTypes.CANCEL,
            label="Cancel",
            custom_id="cancel")
    )
    prompt = await ctx.send(content="Are you sure you want to sell all your items?", components=[row])

    def check(inter_):
        return inter_.author == ctx.author

    try:
        inter = await prompt.wait_for_button_click(check=check, timeout=30)
    except asyncio.TimeoutError:
        # auto cancel
        await prompt.delete()

        return False
    else:
        await prompt.delete()

        if inter.clicked_button.custom_id == "confirm":
            return True

class MarketCog(commands.Cog, name='Market'):
    """Contains market commands that lets players buy/sell items"""

    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def buy(self, ctx:Context, amount: Optional[int] = 1, *,
                  item: Optional[Union[CaseConverter, ItemConverter]]):
        """
        Buy a skin from the market using your balance
        Args:
            amount: quantity of the item you want to buy
            item: item you want to buy, it can be a case, key or an item
        """
        if not item:
            return await ctx.reply(
                content='Item not found or not marketable.',
                mention_author=False
            )

        amount = amount if amount > 0 else 1
        async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
            if able_to_buy(player, item, amount):

                if isinstance(item, (Case, Key)):
                    player.mod_case(item.name, amount) if isinstance(item, Case) else player.mod_key(item.name, amount)


                elif isinstance(item, Item):
                    item: Item
                    generated_stats = [generate_stats(item.exterior) for _ in range(amount)]
                    for stats in generated_stats:
                        player.add_item(item.name, stats) 

                player.balance -= item.price * amount
                await player.save()
                return await ctx.reply(
                    content=f'Purchased {item.name} for ${item.price:.2f}.' if amount == 1 else f'Purchased {amount}x {item.name} for ${item.price * amount:.2f}.',
                    mention_author=False
                )

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def sell(self, ctx, amount:Optional[int] = 1, *,
                   item: Optional[Union[CaseConverter, ItemConverter]]):
        """
        Sell an item to the market and get balance
        Args:
            amount: amount to sell, applies to the specified item
            item: the name of the item you want to sell
        """
        
        if not item:
            return await ctx.reply(
                content='Item not found or not marketable.',
                mention_author=False
            )

        amount = amount if amount > 0 else 1

        async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
            if able_to_sell(player, item, amount):

                fees = await player.fees

                if isinstance(item, Item):
                    item: Item
                    items = player.inventory.get(item.name, [])
                    if amount == len(items):
                        player.inventory.pop(item.name)
                    else:
                        player.inventory[item.name] = random.sample(items, k=len(items)-amount)

                elif isinstance(item, Case):
                    item: Case
                    player.mod_case(item.name, -amount)

                earning = (item.price * fees) * amount
                player.balance += earning

                await player.save()
                await ctx.reply(
                    content=f'Sold {amount}x {item.name} for ${earning:.2f}.' if earning > 0.0 else 'Sold no items.',
                    mention_author=False
                )

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def sellall(self, ctx:Context, operator:Optional[OperatorConverter], *, item_or_price: Optional[Union[float, CaseConverter, ItemConverter]]):
        """
        Bulk sells the specified item or all items if none specified

        Args:
            operator: logical operator to define greater or less price rules
            price: price to use with the specified logical operator
            item: the name of the item you want to sell, leave empty to sell everything (excluding cases)
        \n
        Examples:
            c.sellall: Sell everything
            c.sellall ak jaguar fn: Sell all with name AK-47 | Jaguar (Factory Name)
            c.sellall > 5: Sell all items with price greater than $5.0 (excluding cases)
            c.sellall < 5: Sell all items with price less than $5.0 (excluding cases)
        """
        
        async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
            if not player.trade_banned:

                fees = await player.fees
                earning = 0.0

                # operator specified, price specified, no item specified
                if isinstance(item_or_price, float) and operator:
                    for item in await player.inv_items():
                        item: Item
                        if item.price:
                            if operator(item.price, item_or_price):
                                earning += (item.price * fees) * player.item_count(item.name)
                                player.inventory.pop(item.name)

                # no operator specified, item specified
                if isinstance(item_or_price, Item):
                    if item_or_price in [*player.inventory]:
                        item: Item
                        if item_or_price.price:
                            earning += (item.price * fees) * player.item_count(item.name)
                            player.inventory.pop(item.name)

                # none or invalid arguments passed in, 
                # either an operator, float, Item or Case
                # (sells all items)
                if not operator and not item_or_price:
                    if await sell_prompt(ctx):
                        for item in await player.inv_items():
                            item: Item
                            if item.price:
                                earning += (item.price * fees) * player.item_count(item.name)
                                player.inventory.pop(item.name)
                    else:
                        return

                # operator specified, no item/price specified
                # operator specified, item specified
                # operator not specified, price specified
                if any(
                    {
                        operator and not item_or_price,
                        operator and isinstance(item_or_price, (Item, Case)),
                        not operator and isinstance(item_or_price, float)
                    }
                ):
                    return await ctx.reply(
                        content='There was an error parsing your request.',
                        mention_author=False
                    )

                player.balance += earning
                await player.save()
                await ctx.reply(
                    content=f'Sold items for ${(earning):.2f}.' if earning > 0.0 else 'Sold no items.',
                    mention_author=False
                )
        

    @commands.command(aliases=['inspect'])
    async def price(self, ctx: Context, *, query: Optional[ItemConverter]):
        """
        Shows item price & asset with specified query
        Args:
            query: the name of the item to search
        """
        if query:
            query: Item
            await ctx.send(embed=query.to_embed(minimal=True if ctx.invoked_with == 'price' else False))
        else:
            await ctx.send(embed=Embed(description='Item not found', color=Color.FIRE_ORANGE))

    @commands.cooldown(10, 60, BucketType.member)
    @commands.command()
    async def caseprices(self, ctx: Context):
        """Lists all the cases with their prices next to them"""
        for case in [*all_cases]:
            c = Case(case)
            if c:
                case_prices[case] = c.price
        pages = paginate_to_embeds(description='\n'.join(
            f'{k[:20] + "..." if len(k) > 22 else k}: **${v:.2f}**' for k, v in case_prices.items()),
            title='Case Prices', max_size=200, color=Colour.random())

        paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
        if len(pages) > 1:
            paginator.add_reaction('⬅️', "back")
            paginator.add_reaction('➡️', "next")

        return await paginator.run(pages)

def setup(bot):
    bot.add_cog(MarketCog(bot))
