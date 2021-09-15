import asyncio
from bot.cogs.core import disable_row

from discord.ext.commands.errors import MissingPermissions, NotOwner
from modules.emojis import Emojis
from datetime import datetime, timedelta
from modules.config import OWNERS_IDS
from typing import Optional
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle
from shortuuid import ShortUUID

from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency
from discord.ext import commands

from discord import Embed, Colour, Permissions

from modules.errors import  CheatsDisabled, CodeInvalid
from modules.database.promos import Promo
from modules.database import Guild
from modules.database.players import Player, SafePlayer
from dpytools.embeds import * 

allowed_characters = "ABCDEFGHJKLMNPRSTUVXYZ23456789"

uuid_gen = ShortUUID()
uuid_gen.set_alphabet(''.join(list(allowed_characters)))

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
    @promo.command()
    async def create(self, ctx, code:Optional[str.upper]):
        """Create a promo code | Only works in servers with cheats enabled"""
        if not ctx.author.guild_permissions.administrator and not ctx.author.id in OWNERS_IDS: raise MissingPermissions(['administrator'])
        guild = await Guild.get(True, guild_id=ctx.guild.id)
        if ctx.author.id not in OWNERS_IDS and not guild.server_cheats_enabled: raise CheatsDisabled('This command can\'t be run in servers with cheats disabled.')
        
        messages = []
        responses = []
        responded = False
        code = code if code and ctx.author.id in OWNERS_IDS else uuid_gen.random(length=8)
        def check(m): return m.author == ctx.author and m.channel == ctx.channel

        messages.append(await ctx.send('Please reply with amount of funds you want for this promo'))
        while not responded:
            try:response = await self.bot.wait_for('message', timeout=30, check=check)
            except asyncio.TimeoutError: pass
            if response:
                responded = True
                if str(response.content).isdigit(): funds = min(10000, float(response.content))

                else: return await ctx.send('Invalid input')

        responded = False
        responses.append(response)
        row = ActionRow(Button(style=ButtonStyle.blurple, label='Global', emoji='🌎', disabled=not ctx.author.id in OWNERS_IDS), Button(style=ButtonStyle.green, label='Server', emoji='🌕'))
        messages.append(await ctx.send('Is this a global promo code or a server promo code?', components=[row]))

        try: inter = await messages[-1].wait_for_button_click(check=check, timeout=30)
        except asyncio.TimeoutError: return await messages[-1].edit(components=[disable_row(row)])
        else: is_global = inter.clicked_button.label == 'Global' and ctx.author.id in OWNERS_IDS
        finally: await messages[-1].delete()

        messages.append(await ctx.send('How many times this promo code can be used?'))
        while not responded:
            try:response = await self.bot.wait_for('message', timeout=30, check=check)
            except asyncio.TimeoutError: pass
            finally: responses.append(response)
            if response:
                responded = True
                if str(response.content).isdigit(): max_uses=int(response.content)
            else: return await ctx.send('Invalid input')

        responded = False
        responses.append(response)


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
                else: return await ctx.send('Invalid input')


            else: return await ctx.send('Invalid input')
            
        responded = False
        row = ActionRow(Button(style=ButtonStyle.blurple, label='Yes'), Button(style=ButtonStyle.blurple, label='No'))
        messages.append(await ctx.send('Do you want to restrict usage of this promo code to certain users?', components=[row]))


        try: inter = await messages[-1].wait_for_button_click(check=check, timeout=30)
        except asyncio.TimeoutError: pass
        else:
            await messages[-1].delete()
            is_restricted = inter.clicked_button.label == 'Yes'
            if is_restricted:
                messages.append(await ctx.send('Which users can use this promo code? Please specify user IDs separated by commas, (e.g. 123, 456, 789)'))
                while not responded:
                    try:response = await self.bot.wait_for('message', timeout=30, check=check)
                    except asyncio.TimeoutError: return await messages[-1].edit(components=[disable_row(row)])
                    if response:
                        responded = True
                        available_to = response.content.replace(' ', '').split(',')
                        available_to = [int(uid) for uid in available_to if isinstance(uid, int)]
            else:
                available_to = list()
        finally: 
            responses.append(response)
            
        messages.append(await ctx.send('Attempting to delete messages...'))
        if ctx.guild.me.guild_permissions.manage_messages: 
            for m in messages:
                try: await m.delete()
                except: pass
            for r in responses:
                try: await r.delete()
                except: pass
        else: await ctx.send(f'{Emojis.WARNING.value} I am missing **Manage Messages** permission to delete the messages.')
        
        # prevention of duplicate codes
        existing = await Promo.get(code=code)
        while existing:
            code = uuid_gen.random(length=8)
            existing = await Promo.get(code=code)

        promo = await Promo.get(
            True,
            code = code,
            expires_at = expiration.replace(microsecond=0, second=0) if expire_hours else None,
            funds = funds,
            is_global = is_global,
            available_to = available_to,
            available_in = [] if is_global else [ctx.guild.id],
            max_uses = max_uses
        )
        await promo.save()

        await ctx.send(embed=Embed(
            description = f"""
            Promo **{promo.code}** has been created and is valid until {expiration.replace(microsecond=0, second=0) if expire_hours else 'forever'}.
            Promo can be used by {promo.available_to or 'anyone'} in {'every server' if not promo.available_in else 'in this server'} and everyone can use it only once.
            This promo code has {promo.max_uses} max uses and users will receive **${promo.funds:.2f}** upon redeem.
            """,
            color=Colour.random()
        ))
        

        
        

    @guild_only()
    @max_concurrency(1, BucketType.default, wait=True)
    @promo.command()
    async def use(self, ctx, code:str.upper):
        """Redeems the specified promo code"""
        promo = await Promo.get(code=code)
        if promo:
            temp = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            if promo.eligible_for(temp):
                promo.uses += 1
                promo.users.append(ctx.author.id)
                await promo.save()

                # used promo before waiting for safe player for security and prevent abuse / stealing code

                async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
                    player.balance += promo.funds
                    await player.save()
                    await ctx.send(f'Success! You\'ve received **${promo.funds}**')
            else:
                await ctx.send('You are ineligible for this promo code.')

            return
        raise CodeInvalid('Promo code not found.')
        
    @promo.command()
    async def info(self, ctx, code:str):
        """Shows information about the given promo"""
        promo = await Promo.get(code=code)
        if promo:
            if promo.is_global and ctx.author.id not in OWNERS_IDS: raise NotOwner('You are not allowed to view global promotion codes')
            embed = Embed(color=Colour.random())
            embed.add_fields(inline=False, **{k:', '.join([str(uid) for uid in v]) if isinstance(v, list) else v for k, v in {k:v for k, v in promo if v}.items()})
            await ctx.send(embed=embed)
        else:
            raise CodeInvalid('Promo code not found.')

    @commands.is_owner()
    @promo.command()
    async def delete(self, ctx, code:str):
        """Deletes a promo code"""
        promo = await Promo.get(code=code)
        if promo:
            await promo.delete()
            await ctx.send(f'Deleted `{code}`')
        else:
            raise CodeInvalid('Promo code not found.')



def setup(bot):
    bot.add_cog(PromoCog(bot))
