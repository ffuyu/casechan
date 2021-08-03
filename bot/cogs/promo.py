from datetime import datetime, timedelta
from discord.ext.commands.cooldowns import BucketType

from discord.ext.commands.core import guild_only, max_concurrency

from modules.errors import AlreadyClaimed, CodeClaimed, CodeExpired, CodeInvalid, ExistingCode
from modules.database.promos import Promo
from modules.database.players import Player

from typing import Optional

from discord.ext import commands

from shortuuid import ShortUUID

allowed_characters = [
    'A', 'B', 'C', 'D', 'E',
    'F', 'G', 'H', 'J', 'K',
    'L', 'M', 'N', 'P', 'R',
    'S', 'T', 'V', 'X', 'Y',
    'Z', '2', '3', '4', '5',
    '6', '7', '8', '9'
    ]

uuid_gen = ShortUUID()
uuid_gen.set_alphabet(''.join(allowed_characters))

class PromoCog(commands.Cog, name='Promo Codes'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    
    @commands.group(hidden=True)
    async def promo(self, ctx):
        pass
    
    @commands.is_owner()
    @promo.command()
    async def create(self, ctx, code:Optional[str.upper], funds:Optional[int], max_uses:Optional[int]=1, valid_hours:Optional[float]=None):
        if code.is_digit():
            funds = code
            code = uuid_gen.random(10).upper()
            
        code = code or uuid_gen.random(10).upper()
        funds = funds or 25
        promo = await Promo.get(code=code)
        if not promo:
            promo = await Promo.get(True, code=code, funds=funds, max_uses=max_uses, expires_at=(datetime.utcnow() + timedelta(hours=valid_hours)) if valid_hours else None)
            await ctx.send(f'Created promo code `{promo.code}`')
            await promo.save()
        else:
            raise ExistingCode('This promo code already exists!')

    @guild_only()
    @max_concurrency(1, BucketType.default, wait=True)
    @promo.command()
    async def use(self, ctx, code:str.upper):
        promo = await Promo.get(code=code)
        if promo:
            if not promo.is_expired:
                if not promo.uses >= promo.max_uses:
                    if not ctx.author.id in promo.users:

                        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
                        player.balance += promo.funds
                        promo.uses += 1
                        promo.users.append(ctx.author.id)
                        await promo.save()
                        await player.save()
                        return await ctx.send(f'Success! You\'ve received **${promo.funds}**')

                    raise AlreadyClaimed('You have already used this promo code.')
                raise CodeClaimed('This promo code has reached max uses.')
            raise CodeExpired('This promo code has expired.')
        raise CodeInvalid('Promo code not found.')
        


def setup(bot):
    bot.add_cog(PromoCog(bot))
