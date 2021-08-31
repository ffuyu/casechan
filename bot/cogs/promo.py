from datetime import datetime, timedelta
from typing import Optional
from shortuuid import ShortUUID

from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency
from discord.ext import commands

from discord import Embed, Colour

from modules.errors import AlreadyClaimed, CodeClaimed, CodeExpired, CodeInvalid, ExistingCode
from modules.database.promos import Promo
from modules.database.players import Player, SafePlayer



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
    
    @commands.cooldown(10, 60, BucketType.user)
    @commands.is_owner()
    @promo.command()
    async def create(self, ctx, code:Optional[str.upper], funds:Optional[int], max_uses:Optional[int]=1, valid_hours:Optional[float]=None):
        if code and code.isdigit():
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
                        
                        promo.uses += 1
                        promo.users.append(ctx.author.id)
                        await promo.save()

                        async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
                            player.balance += promo.funds
                            
                            await player.save()
                            return await ctx.send(f'Success! You\'ve received **${promo.funds}**')

                    raise AlreadyClaimed('You have already used this promo code.')
                raise CodeClaimed(f'This promo code has reached max uses. ({promo.uses}/{promo.max_uses})')
            raise CodeExpired('This promo code has expired.')
        raise CodeInvalid('Promo code not found.')
        

    @promo.command()
    async def info(self, ctx, code:str, show_users:Optional[bool]):
        promo = await Promo.get(code=code)
        if promo:
            embed = Embed(
                color=Colour.random()
            )
            embed.timestamp = promo.expires_at
            embed.add_field(name='Funds', value=promo.funds)
            embed.add_field(name='Uses', value=f'{promo.uses}/{promo.max_uses}')

            if show_users and promo.uses:
                embed.add_field(name='Users', value='\n'.join([str(uid) for uid in promo.users]), inline=False)

            await ctx.send(embed=embed)
        else:
            raise CodeInvalid('Promo code not found.')

    @promo.command()
    async def delete(self, ctx, code:str):
        promo = await Promo.get(code=code)
        if promo:
            await promo.delete()
            await ctx.send(f'Deleted `{code}`')
        else:
            raise CodeInvalid('Promo code not found.')



def setup(bot):
    bot.add_cog(PromoCog(bot))
