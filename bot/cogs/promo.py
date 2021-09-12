import asyncio
from modules.emojis import Emojis
from bot.cogs.core import disable_row
from datetime import datetime, timedelta
from modules.config import OWNERS_IDS
from typing import Optional
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle
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
    async def create(self, ctx, code:Optional[str.upper]):
        messages = []
        responses = []
        responded = False
        code = code or uuid_gen.random(length=8)
        def check(m): return m.author == ctx.author and m.channel == ctx.channel
        messages.append(await ctx.send('Please reply with amount of funds you want for this promo'))
        while not responded:
            try:response = await self.bot.wait_for('message', timeout=30, check=check)
            except asyncio.TimeoutError: pass
            if response:
                responded = True
                if str(response.content).isdigit(): funds = float(response.content)

                else: return await ctx.send('Invalid user input. Aborting...')

        responded = False
        row = ActionRow(Button(style=ButtonStyle.blurple, label='Global', emoji='🌎', disabled=not ctx.author.id in OWNERS_IDS), Button(style=ButtonStyle.green, label='Server', emoji='🌕'))
        messages.append(await ctx.send('Is this a global promo code or a server promo code?', components=[row]))

        try: inter = await messages[-1].wait_for_button_click(check=check, timeout=30)
        except asyncio.TimeoutError: return await ctx.send('No user input. Aborting...')
        else: is_global = inter.clicked_button.label == 'Global'
        finally: await messages[-1].edit(components=[disable_row(row)])

        messages.append(await ctx.send('How many times this promo code can be used?'))
        while not responded:
            try:response = await self.bot.wait_for('message', timeout=30, check=check)
            except asyncio.TimeoutError: pass
            finally: responses.append(response)
            if response:
                responded = True
                if str(response.content).isdigit(): max_uses=int(response.content)
            else: return await ctx.send('Invalid user input. Aborting...')
        responded = False
        messages.append(await ctx.send('In how many hours will this promo code expire?'))
        while not responded:
            try:response = await self.bot.wait_for('message', timeout=30, check=check)
            except asyncio.TimeoutError: pass
            finally: responses.append(response)
            if response:
                responded = True
                if str(response.content).isdigit(): 
                    expire_hours = float(response.content)
                    expiration = datetime.now() + timedelta(hours=expire_hours)
                else: return await ctx.send('Invalid user input. Aborting...')


            else: return await ctx.send('Invalid user input. Aborting...')
            
        responded = False
        row = ActionRow(Button(style=ButtonStyle.green, label='Yes'), Button(style=ButtonStyle.red, label='No'))
        messages.append(await ctx.send('Do you want to restrict usage of this promo code to certain users?', components=[row]))


        try: inter = await messages[-1].wait_for_button_click(check=check, timeout=30)
        except asyncio.TimeoutError: return await ctx.send('No user input. Aborting...')
        else:
            is_restricted = inter.clicked_button.label == 'Yes'
            if is_restricted:
                messages.append(await ctx.send('Which users can use this promo code? Please specify user IDs separated by commas, (e.g. 123, 456, 789)'))
                while not responded:
                    try:response = await self.bot.wait_for('message', timeout=30, check=check)
                    except asyncio.TimeoutError: pass
                    if response:
                        responded = True
                        available_to = response.content.replace(' ', '').split(',')
                        available_to = [int(uid) for uid in available_to if isinstance(uid, int)]
            else:
                available_to = list()
        finally: 
            responses.append(response)
        
        await messages[-1 if not is_restricted else -2].edit(components=[disable_row(row)]) 
            
        messages.append(await ctx.send('Attempting to delete messages...'))
        if ctx.guild.me.guild_permissions.manage_messages: 
            for m in messages: await m.delete()
        else: await ctx.send(f'{Emojis.WARNING.value} I am missing **Manage Messages** permission to delete the messages.')
        
        promo = await Promo.get(
            True,
            code = code,
            expires_at = expiration,
            funds = funds,
            is_global = is_global,
            available_to = available_to,
            available_in = [] if is_global else [ctx.guild.id],
            max_uses = max_uses
        )

        await ctx.send(embed=Embed(
            description = f"""
            Promo **{promo.code}** has been created and is valid until {promo.expires_at.replace(microsecond=0, second=0) or 'forever'}.
            Promo can be used by {promo.available_to or 'anyone'} in {'every server' if not promo.available_in else 'in this server'} and everyone can use it only once.
            This promo code has {promo.max_uses} max uses and users will receive **${promo.funds:.2f}** upon redeem.
            """
        ),color=Colour.random())
        

        
        

    @guild_only()
    @max_concurrency(1, BucketType.default, wait=True)
    @promo.command()
    async def use(self, ctx, code:str.upper):
        promo = await Promo.get(code=code)
        if promo:
            temp = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            if promo.eligible_for(temp):
                promo.uses += 1
                promo.users.append(ctx.author.id)
                await promo.save()

            # used promo before waiting for safe player for security and prevent abuse / stealing code

            async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
                if promo.eligible_for(player):
                    player.balance += promo.funds
                    await player.save()
                    await ctx.send(f'Success! You\'ve received **${promo.funds}**')
                else:
                    await ctx.send('You are ineligible for this promo code.')

            return
        raise CodeInvalid('Promo code not found.')
        

    @promo.command()
    async def info(self, ctx, code:str, show_users:Optional[bool]):
        promo = await Promo.get(code=code)
        if promo:
            embed = Embed(
                color=Colour.random()
            )
            if promo.expires_at:
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
