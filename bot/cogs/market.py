import random

from typing import Optional, Union

from modules.errors import ExceededBuyLimit, InsufficientBalance, ItemMissingPrice, ItemMissingStats, ItemNotFound, ItemUnavailable, MissingItem, MissingSpace, NotMarketable, NotTradeable, StateNotEqual, TradeNotAllowed
from modules.cases import Case, Key
from modules.utils.item_converter import ItemConverter
from modules.utils.case_converter import CaseConverter
from modules.utils.key_converter import KeyConverter
from modules.database.players import Player
from modules.database.items import Item

from discord.ext import commands
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.core import guild_only, max_concurrency
from discord.ext.commands.cooldowns import BucketType


def generate_stats(exterior:str):
    ranges = {
        "Battle-Scarred": (0.44, 0.99),
        "Well-Worn": (0.37, 0.439),
        "Field-Tested": (0.85, 0.369),
        "Minimal Wear": (0.07, 0.149),
        "Factory New": (0.00, 0.069)
    }
    range = ranges.get(exterior)
    float_ = random.SystemRandom().uniform(a=range[0], b=range[1])
    seed = random.SystemRandom().randint(1, 1000)
    return float_, seed

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
    async def buy(self, ctx, amount:Optional[int]=1, *, item:Optional[Union[ItemConverter, CaseConverter, KeyConverter]]):
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
                                stats = generate_stats(item.name[item.name.find('(')+1:item.name.find(')')])
                                player.add_item(item.name, stats)
                                print(stats)
                            player.balance -= (item.price * amount)

                            await player.save()
                            return await ctx.send('You have purchased **{}x {}** successfully. You have been charged **${:.2f}**.'.format(amount, item.name, item.price * amount))

                        raise ItemUnavailable('You cannot buy this item now. Reason: Item has no price data.')
                    raise TradeNotAllowed('You cannot buy this item now. Reason: Account trade banned.') 
                raise MissingSpace('You cannot buy this item now. Reason: Inventory limit reached.')
            raise InsufficientBalance('You cannot buy this item now. Reason: Insufficient balance.')
        

        # These instances are intentionally separated due to case prices will have some complex stuff going in them separately.

        if isinstance(item, Case):
            if not player.trade_banned:
                if player.balance >= (0.00 * amount):
                    
                    player.mod_case(item.name, amount)
                    player.balance -= (0.00 * amount)
                    await player.save()

                    return await ctx.send('You have purchased **{}x {}** successfully. You have received this item for **free**'.format(amount, item.name))
                    # return await ctx.send('You have purchased **{}x {}** successfully. You have been charged **${:.2f}**.'.format(amount, item.name, 0.0 * amount))
                
                raise InsufficientBalance('You cannot buy this item now. Reason: Insufficient balance.')
            raise TradeNotAllowed('You cannot buy this item now. Reason: Account trade banned.') 

        if isinstance(item, Key):
            if not player.trade_banned:
                if player.balance >= (0.00 * amount):
                
                    player.mod_key(item.name, amount)
                    player.balance -= (0.00 * amount)
                    await player.save()

                    return await ctx.send('You have purchased **{}x {}** successfully. You have received this item for **free**'.format(amount, item.name))
                    # return await ctx.send('You have purchased **{}x {}** successfully. You have been charged **${:.2f}**.'.format(amount, item.name, 0.0 * amount))

                raise InsufficientBalance('You cannot buy this item now. Reason: Insufficient balance.')
            raise TradeNotAllowed('You cannot buy this item now. Reason: Account trade banned.')     

        raise ItemNotFound('Item not found')

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def sell(self, ctx, *, item:Optional[Union[KeyConverter, CaseConverter, ItemConverter]]):
        """
        Sell a skin to the market and get balance
        Args:
            item: the name of the item you want to sell
        """
        amount = 1
        if isinstance(item, Item):
            player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            if player.item_count(item.name) >= amount:
                if not player.trade_banned:
                    if item.price > 0.00:
            
                        stats = player.inventory.get(item.name, [])
                        if stats:
                            player.rem_item(item.name, stats[0])
                            player.balance += ((item.price * amount) * 0.85)
                            await player.save()
                            return await ctx.send('You have sold **{}x {}** and received **${:.2f}**.'.format(amount, item.name, ((item.price * 0.85) * amount)))
                            
                        raise ItemMissingStats('An error occured while selling your item. Perhaps the item is corrupted.')
                    raise ItemMissingPrice('You cannot sell this item now. Reason: Item has no price data.')
                raise TradeNotAllowed('You cannot sell items. Reason: Account trade banned.')
            raise MissingItem('You cannot sell this item now. Reason: Item not found on inventory.')

        if isinstance(item, (Case, Key)):
            raise NotMarketable('This item cannot be sold.')

        raise ItemNotFound('Item not found.')

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def sellall(self, ctx, *, item:Optional[Union[ItemConverter, CaseConverter, KeyConverter]]):
        """
        Bulk sells the specified item or all items if none specified
        Args:
            item: the name of the item you want to sell, leave empty to sell everything
        """
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        if isinstance(item, Item):
            amount = player.item_count(item.name)
            if amount:
                player.inventory.pop(item.name)
                player.balance += (item.price * 0.85)
                await player.save()
                return await ctx.send('You have sold **{}x {}(s)** and received **${:.2f}**.'.format(amount, item.name, ((item.price * 0.85) * amount)))
            raise MissingItem('You don\'t have any **{}** to sell.'.format(item.name))

        if isinstance(item, (Case, Key)):
            raise NotMarketable('This item cannot be sold.')

        if not item:
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
                            player.balance += ((item_.price * 0.85) * amount)
                            total_received += ((item_.price * 0.85) * amount)
                        
                await player.save()
                return await ctx.send('You have sold **{} items** and received **${:.2f}**.'.format(total_items, total_received))
            raise ItemNotFound('You have no items to sell.')
        raise ItemNotFound('Item not found.')
        
def setup(bot):
    bot.add_cog(MarketCog(bot))
