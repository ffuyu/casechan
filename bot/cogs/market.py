import asyncio
from modules.constants import ButtonCancel, ButtonConfirm
from DiscordUtils.Pagination import CustomEmbedPaginator
from discord.colour import Colour
from discord.embeds import Embed
from discord.ext.commands.context import Context
from discord.ext.commands.errors import MissingRequiredArgument
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle
from dpytools import Color
from dpytools.embeds import paginate_to_embeds
from modules.database import engine
from modules.database.users import UserData
from typing import Optional, Union

from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency

from modules.cases import Case, Key, all_cases
from modules.database.items import Item, generate_stats
from modules.database.players import Player, SafePlayer
from modules.errors import ExceededBuyLimit, InsufficientBalance, ItemMissingPrice, ItemMissingStats, ItemNotFound, \
    ItemUnavailable, MissingItem, MissingSpace, NotMarketable, SaleNotConfirmed, TradeNotAllowed
from modules.utils.case_converter import CaseConverter
from modules.utils.item_converter import ItemConverter
from modules.utils.key_converter import KeyConverter
from modules.utils.operator_converter import OperatorConverter

case_prices = {}

async def sell_prompt(ctx):
    row = ActionRow(
        Button(
            style=ButtonConfirm,
            label="Confirm",
            custom_id="confirm"),
        Button(
            style=ButtonCancel,
            label="Cancel",
            custom_id="cancel")
    )
    prompt = await ctx.send(content="Do you confirm this sale?", components=[row])

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
        else:
            return False

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
                  item: Optional[Union[CaseConverter, KeyConverter, ItemConverter]]):
        """
        Buy a skin from the market using your balance
        Args:
            amount: quantity of the item you want to buy
            item: item you want to buy, it can be a case, key or an item
        """
        amount = amount if amount > 1 else 1
        if amount > 1000:
            raise ExceededBuyLimit('You can\'t buy more than 1000 items at once.')

        async with SafePlayer(ctx.author.id, ctx.guild.id) as player:

            if isinstance(item, Item):
                if player.balance >= (item.price * amount):
                    if (1000 - len(player.inventory)) >= amount:
                        if not player.trade_banned:
                            if item.price > 0.00:

                                for _ in range(amount):
                                    stats = generate_stats(item.name[item.name.find('(') + 1:item.name.find(')')])
                                    player.add_item(item.name, stats)
                                player.balance -= (item.price * amount)

                                await player.save()
                                return await ctx.send(
                                    'You have purchased **{}x {}** successfully. You have been charged **${:.2f}**.'.format(
                                        amount, item.name, item.price * amount))

                            raise ItemUnavailable('You cannot buy this item now. Reason: Item has no price data.')
                        raise TradeNotAllowed('You cannot buy this item now. Reason: Account trade banned.')
                    raise MissingSpace('You cannot buy this item now. Reason: Inventory limit reached.')
                raise InsufficientBalance('You cannot buy this item now. Reason: Insufficient balance.')

            if isinstance(item, Case):

                item_ = await Item.get(name=item.name)
                if item_:
                    price = item_.price

                    if not player.trade_banned:
                        if player.balance >= (price * amount):
                            player.mod_case(item.name, amount)
                            player.balance -= (price * amount)
                            await player.save()

                            item.price = await Item.get(name=item.name)

                            receipt = await ctx.send(
                                'You have purchased **{}x {}** for **${:.2f}**'.format(
                                    amount, item.name, price * amount))

                            def check(inter_):
                                return inter_.author == ctx.author

                            row = ActionRow(
                                Button(
                                    style=ButtonConfirm,
                                    label="Yes",
                                    custom_id="yes",
                                ),
                                Button(
                                    style=ButtonCancel,
                                    label="No",
                                    custom_id="no",
                                )
                            )
                            message = await ctx.send(f"Would you like to buy **{amount}x {item.key}**?", components=[row])

                            try:
                                inter = await message.wait_for_button_click(check=check, timeout=30)
                            except asyncio.TimeoutError:
                                pass
                            else:
                                if inter.clicked_button.custom_id == "yes":
                                    if player.balance >= (amount * 2.5):
                                        key = Key(item.key)
                                        player.mod_key(item.key, amount)
                                        player.balance -= (amount * key.price)
                                        await player.save()
                                        await receipt.edit(content='You have purchased **{}x {}** and keys for **${:.2f}**'.format(
                                    amount, item.name, (price * amount) + (amount * key.price)))
                                    else:
                                        raise InsufficientBalance('You cannot buy this item now. Reason: Insufficient balance.')
                            finally:
                                await message.delete()
                                return 

                        raise InsufficientBalance('You cannot buy this item now. Reason: Insufficient balance.')
                    raise TradeNotAllowed('You cannot buy this item now. Reason: Account trade banned.')
                raise ItemMissingPrice("This case cannot be bought right now. Please try again later.")

            if isinstance(item, Key):
                if not player.trade_banned:
                    if player.balance >= (item.price * amount):
                        player.mod_key(item.name, amount)
                        player.balance -= (item.price * amount)
                        await player.save()


                        return await ctx.send(
                            'You have purchased **{}x {}** for **${:.2f}**'.format(
                                amount, item.name, item.price * amount))

                    raise InsufficientBalance('You cannot buy this item now. Reason: Insufficient balance.')
                raise TradeNotAllowed('You cannot buy this item now. Reason: Account trade banned.')

            raise ItemNotFound('Item not found')

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def sell(self, ctx, *, item: Optional[Union[CaseConverter, KeyConverter, ItemConverter]]):
        """
        Sell a skin to the market and get balance
        Args:
            item: the name of the item you want to sell
        """
        amount = 1
        if isinstance(item, Item):
            async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
                user = await UserData.get(True, user_id=ctx.author.id)
                fees = user.fees
                if player.item_count(item.name) >= amount:
                    if not player.trade_banned:
                        if item.price > 0.00:
                            stats = player.inventory.get(item.name, [])
                            if stats:

                                if item.price >= 1000:
                                    if not await sell_prompt(ctx):
                                        raise SaleNotConfirmed("User cancelled the sale or failed to respond in time.")
                                
                                player.rem_item(item.name, stats[0])
                                player.balance += ((item.price * amount) * fees)
                                player.stats['transactions']['items_sold'] += 1
                                await player.save()
                                return await ctx.send(
                                    'You have sold **{}x {}** and received **${:.2f}**.'.format(amount, item.name, (
                                                (item.price * fees) * amount)))

                            raise ItemMissingStats('An error occured while selling your item. '
                                                   'Perhaps the item is corrupted.')
                        raise ItemMissingPrice('You cannot sell this item now. Reason: Item has no price data.')
                    raise TradeNotAllowed('You cannot sell items. Reason: Account trade banned.')
                raise MissingItem('You cannot sell this item now. Reason: Item not found on inventory.')

        if isinstance(item, (Case, Key)):
            raise NotMarketable('This item cannot be sold.')

        raise ItemNotFound('Please specify an item to sell')

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def sellall(self, ctx, operator:Optional[OperatorConverter], price:Optional[float], *, item: Optional[Union[CaseConverter, KeyConverter, ItemConverter]]):
        """
        Bulk sells the specified item or all items if none specified

        Args:
            operator: logical operator to define greater, less or equal price rules
            price: price to use with the specified logical operator
            item: the name of the item you want to sell, leave empty to sell everything
        \n
        Examples:
            c.sellall: Sell everything
            c.sellall ak jaguar fn: Sell all with name AK-47 | Jaguar (Factory Name)
            c.sellall > 5: Sell all items with price greater than $5.0
            c.sellall < 5: Sell all items with price less than $5.0
        """
        
        user = await UserData.get(True, user_id=ctx.author.id)
        fees = user.fees
        to_sell = {}
        async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
            if player.trade_banned:
                raise TradeNotAllowed('You cannot sell items. Reason: Account trade banned.')
            if isinstance(item, Item):
                amount = player.item_count(item.name)
                if amount:

                    player.inventory.pop(item.name)
                    player.balance += (item.price * fees)
                    player.stats['transactions']['items_sold'] += amount
                    await player.save()
                    return await ctx.send('You have sold **{}x {}(s)** and received **${:.2f}**.'.format(amount, item.name,
                                                                                                        ((
                                                                                                                    item.price * fees) * amount)))
                raise MissingItem('You don\'t have any **{}** to sell.'.format(item.name))

            if isinstance(item, (Case, Key)):
                raise NotMarketable('This item cannot be sold.')

            if not item and not operator and not price:
                items_count = sum([len(stats) for _, stats in player.inventory.items()])
                if items_count:

                    for item in player.inventory:
                        item_ = await Item.get(False, name=item)
                        if item_:
                            to_sell.setdefault(item_.name, player.item_count(item) * (fees * item_.price))
                    
                    if sum(list(to_sell.values())) >= 1000:
                        if not await sell_prompt(ctx):
                            raise SaleNotConfirmed("User cancelled the sale or failed to respond in time.")

                    for name, price in to_sell.items():
                        player.inventory.pop(name)
                        player.balance += price

                    player.stats['transactions']['items_sold'] += items_count

                    await player.save()
                    return await ctx.send(
                        'You have sold **{} items** and received **${:.2f}**.'.format(len(to_sell), sum(list(to_sell.values()))))

                raise ItemNotFound('You have no items to sell.')

            elif operator and not price:
                raise MissingRequiredArgument(price)
            elif operator and price:
                price = price if price > 0 else 1
                items = player.inventory
                items_count = sum([len(stats) for _, stats in player.inventory.items()])
                to_sell_count = 0
                if not items:
                    raise ItemNotFound('You have no items to sell.')

                if operator == ">":

                    for item in player.inventory:
                        item_ = await Item.get(False, name=item)
                        if item_:
                            if item_.price > price:
                                to_sell_count += 1 * player.item_count(item)
                                to_sell.setdefault(item_.name, player.item_count(item) * (fees * item_.price))
                    
                    if sum(list(to_sell.values())) >= 1000:
                        if not await sell_prompt(ctx):
                            raise SaleNotConfirmed("User cancelled the sale or failed to respond in time.")

                    for name, price in to_sell.items():
                        player.inventory.pop(name)
                        player.balance += price
                        

                    player.stats['transactions']['items_sold'] += items_count

                elif operator == "<":
                    
                    for item in player.inventory:
                        item_ = await Item.get(False, name=item)
                        if item_:
                            if item_.price < price:
                                to_sell_count += 1 * player.item_count(item)
                                to_sell.setdefault(item_.name, player.item_count(item) * (fees * item_.price))
                    
                    if sum(list(to_sell.values())) >= 1000:
                        if not await sell_prompt(ctx):
                            raise SaleNotConfirmed("User cancelled the sale or failed to respond in time.")

                    for name, price in to_sell.items():
                        player.inventory.pop(name)
                        player.balance += price

                    player.stats['transactions']['items_sold'] += items_count
                
                if to_sell:
                    await player.save()
                    return await ctx.send(
                        'You have sold **{} items** and received **${:.2f}**.'.format(to_sell_count, sum(list(to_sell.values()))))

                raise MissingItem("You don't have any items to sell within the specified price range.")

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
            await ctx.send(embed=Embed(description='Item not found', color=Color.RED))

    @commands.cooldown(10, 60, BucketType.member)
    @commands.command()
    async def caseprices(self, ctx: Context):
        """List the cases you currently have."""
        if not case_prices:
            for case in all_cases:
                c = await Item.get(name=case)
                if c:
                    case_prices[case] = c.price
        pages = paginate_to_embeds(description='\n'.join(
            f'{k[:20] + "..." if len(k) > 22 else k}: **${v}**' for k, v in case_prices.items()),
            title='Case Prices', max_size=200, color=Colour.random())

        paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
        if len(pages) > 1:
            paginator.add_reaction('⬅️', "back")
            paginator.add_reaction('➡️', "next")

        return await paginator.run(pages)

def setup(bot):
    bot.add_cog(MarketCog(bot))
