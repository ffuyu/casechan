import os
from discord.ext.commands.cooldowns import BucketType
from modules.utils.item_converter import ItemConverter
from typing import Optional
from discord.ext import commands
from modules.database.players import Player
from modules.database.items import Item
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.core import guild_only, max_concurrency
from bot.cogs.core import _case
import random


def generate_float(exterior:str) -> float:
    ranges = {
        "Battle-Scarred": (0.44, 0.99),
        "Well-Worn": (0.37, 0.439),
        "Field-Tested": (0.15, 0.369),
        "Minimal Wear": (0.07, 0.149),
        "Factory New": (0.00, 0.069)
    }
    range = ranges.get(exterior)
    print(range)
    return random.SystemRandom().uniform(a=range[0], b=range[1])


class MarketCog(commands.Cog, name='Market'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def buy(self, ctx, amount:Optional[int]=1, *, item:Optional[ItemConverter]):
        """Buy a skin from the market using your balance"""
        amount = amount if amount > 1 else 1
        if item:
            player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            await ctx.send(generate_float(item.name[item.name.find('(')+1:item.name.find(')')]))
            if player.balance >= (item.price * amount):
                if (1000 - len(player.inv_items())) >= amount:
                    if not player.trade_banned:
                        if item.price > 0.00:
                            
                            player.add_item(item.name, (generate_float(), random.SystemRandom().randint(0, 1000)))
                            player.balance -= (item.price * amount)
                            player.save()
                            return await ctx.send(f'You have purchased **{amount}x {item.name}** successfully. You have been charged {item.price * amount}')

                        return await ctx.send('You cannot buy this item now. Reason: Item has no price data.')
                    return await ctx.send('You cannot buy this item now. Reason: Account trade banned.') 
                return await ctx.send('You cannot buy this item now. Reason: Inventory limit reached.')
            return await ctx.send('You cannot buy this item now. Reason: Insufficient balance.')

        return await ctx.send('Item not found')

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def sell(self, ctx, amount:Optional[int]=1, *, item:Optional[ItemConverter]):
        """Sell a skin to the market and get balance"""
        amount = amount if amount > 1 else 1
        if item:
            player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            if item.name in [x.name for x in await player.inv_items()]:
                if not player.trade_banned:
                    if item.price > 0.00:
                        
                        # player.add_item(item.name, (generate_float(), random.SystemRandom().randint(0, 1000))) # TODO Replace with remove_item function
                        player.balance += ((item.price * amount) * 0.15)
                        await player.save()
                        return await ctx.send('You have sold **{}x {}** successfully. You have received ${:.2f}.'.format(amount, item.name, ((item.price * amount) * 0.15)))

                    return await ctx.send('You cannot sell this item now. Reason: Item has no price data.')
                return await ctx.send('You cannot sell this item now. Reason: Account trade banned.')
            return await ctx.send('You cannot sell this item now. Reason: Item not found on inventory.')

        return await ctx.send('Item not found')


def setup(bot):
    bot.add_cog(MarketCog(bot))
