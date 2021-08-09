from discord.ext.commands.errors import MissingRequiredArgument
from modules.database.users import UserData
from typing import Optional, Union

from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency

from modules.cases import Case, Key
from modules.database.items import Item, generate_stats
from modules.database.players import Player
from modules.errors import ExceededBuyLimit, InsufficientBalance, ItemMissingPrice, ItemMissingStats, ItemNotFound, \
    ItemUnavailable, MissingItem, MissingSpace, NotMarketable, TradeNotAllowed
from modules.utils.case_converter import CaseConverter
from modules.utils.item_converter import ItemConverter
from modules.utils.key_converter import KeyConverter
from modules.utils.operator_converter import OperatorConverter

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
    async def buy(self, ctx, amount: Optional[int] = 1, *,
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

        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)

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
            price = item_.price

            if not player.trade_banned:
                if player.balance >= (price * amount):
                    player.mod_case(item.name, amount)
                    player.balance -= (price * amount)
                    await player.save()

                    item.price = await Item.get(name=item.name)

                    return await ctx.send(
                        'You have purchased **{}x {}** for **${}**'.format(
                            amount, item.name, price))

                raise InsufficientBalance('You cannot buy this item now. Reason: Insufficient balance.')
            raise TradeNotAllowed('You cannot buy this item now. Reason: Account trade banned.')

        if isinstance(item, Key):
            if not player.trade_banned:
                if player.balance >= (item.price * amount):
                    player.mod_key(item.name, amount)
                    player.balance -= (item.price * amount)
                    await player.save()


                    return await ctx.send(
                        'You have purchased **{}x {}** for **${}**'.format(
                            amount, item.name, item.price))

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
            player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            user = await UserData.get(True, user_id=ctx.author.id)
            fees = user.fees
            if player.item_count(item.name) >= amount:
                if not player.trade_banned:
                    if item.price > 0.00:

                        stats = player.inventory.get(item.name, [])
                        if stats:
                            player.rem_item(item.name, stats[0])
                            player.balance += ((item.price * amount) * fees)
                            player.stats['transactions']['items_sold'] += 1
                            await player.save()
                            return await ctx.send(
                                'You have sold **{}x {}** and received **${:.2f}**.'.format(amount, item.name, (
                                            (item.price * fees) * amount)))

                        raise ItemMissingStats(
                            'An error occured while selling your item. Perhaps the item is corrupted.')
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
            c.sellall = 5: Sell all items that are worth $5.0-5.99
        """
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        user = await UserData.get(True, user_id=ctx.author.id)
        fees = user.fees
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
            items = list(player.inventory.keys())
            if items:
                total_received = 0.0
                total_items = 0
                for item in items:
                    amount = player.item_count(item)
                    total_items += amount
                    if amount:
                        item_ = await Item.get(False, name=item)
                        if item_:
                            player.inventory.pop(item_.name)
                            player.balance += ((item_.price * fees) * amount)
                            player.stats['transactions']['items_sold'] += amount
                            total_received += ((item_.price * fees) * amount)

                await player.save()
                return await ctx.send(
                    'You have sold **{} items** and received **${:.2f}**.'.format(total_items, total_received))
            raise ItemNotFound('You have no items to sell.')

        elif operator and not price:
            raise MissingRequiredArgument(price)
        elif operator and price:
            items = list(player.inventory.keys())
            if not items:
                raise ItemNotFound('You have no items to sell.')
            total_received = 0.0
            total_items = 0
            if operator == ">":
            
                for item in items:
                    item_ = await Item.get(False, name=item)
                    if not item_.price > price:
                        continue
                    amount = player.item_count(item)
                    total_items += amount
                    if amount:
                        if item_:
                            player.inventory.pop(item_.name)
                            player.balance += ((item_.price * fees) * amount)
                            player.stats['transactions']['items_sold'] += amount
                            total_received += ((item_.price * fees) * amount)

            elif operator == "<":

                for item in items:
                    item_ = await Item.get(False, name=item)
                    if not item_.price < price:
                        continue
                    amount = player.item_count(item)
                    total_items += amount
                    if amount:
                        if item_:
                            player.inventory.pop(item_.name)
                            player.balance += ((item_.price * fees) * amount)
                            player.stats['transactions']['items_sold'] += amount
                            total_received += ((item_.price * fees) * amount)

            elif operator == "=":
                
                for item in items:
                    item_ = await Item.get(False, name=item)
                    if not int(item_.price) == int(price):
                        continue
                    amount = player.item_count(item)
                    total_items += amount
                    if amount:
                        if item_:
                            player.inventory.pop(item_.name)
                            player.balance += ((item_.price * fees) * amount)
                            player.stats['transactions']['items_sold'] += amount
                            total_received += ((item_.price * fees) * amount)


            await player.save()
            return await ctx.send(
                'You have sold **{} items** and received **${:.2f}**.'.format(total_items, total_received))


def setup(bot):
    bot.add_cog(MarketCog(bot))
