
import random

from bot.cogs.core import disable_row
from typing import Optional, Union

from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency
from discord.ext import commands

from discord.colour import Colour
from discord import Embed

from dislash.interactions.message_components import Button, ActionRow
from dislash.interactions.slash_interaction import Interaction

from modules.utils.case_converter import CaseConverter
from modules.utils.key_converter import KeyConverter
from modules.cases import Case, Key
from modules.database import Player
from modules.errors import InsufficientBalance, MissingCase, MissingKey

class GamblingCog(commands.Cog, name='Gambling'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command(aliases=['casehunt', 'keyhunt', 'gamble', 'bet'])
    async def hunt(self, ctx, amount:Optional[Union[int, float]]=1, *, item:Optional[Union[CaseConverter, KeyConverter, int]]):
        """
        Gamble your cases, keys or your balance!
        Args:
            amount: amount of case/key you want to bet
            item: item you want to bet, it can be a case, key or the amount of money
        """
        amount = amount if amount > 1 else 1
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        reward_place = random.randint(1, 9)
        print(reward_place)
        rows = []
        color = 4

        if isinstance(item, Case):
            item: Case
            if not player.cases[item.name] >= amount:
                raise MissingCase(f'You are missing **{amount}x {item.name}** to place a bet.')
            quest_message = 'Guess and press the correct button, win **{}x {}**!'.format(amount*9, item.name)
            win_message = 'You\'ve won **x{}** **{}**!'.format(amount*9, item.name)
            loss_message = 'You\'ve lost **x{} {}**!'.format(amount, item.name)

            player.mod_case(item.name, amount)
            

        if isinstance(item, Key):
            item: Key
            if not player.keys[item.name] >= amount:
                raise MissingCase(f'You are missing **{amount}x {item.name}** to place a bet.')
            quest_message = 'Guess and press the correct button, win **{}x {}**!'.format(amount*9, item.name)
            win_message = 'You\'ve won **x{}** **{}**!'.format(amount*9, item.name)
            loss_message = 'You\'ve lost **x{} {}**!'.format(amount, item.name)
            
            player.mod_key(item.name, amount)


        if not item and amount:
            item = amount
            if not player.balance >= item:
                raise InsufficientBalance('You have insufficient balance to place this bet.')
            quest_message = 'Guess and press the correct button, win **${}**!'.format(item*2)
            win_message = 'You\'ve won **${}**!'.format(2*item)
            loss_message = 'You\'ve lost **${}**!'.format(item)
            
            player.balance -= item


        for y in range(3): 
            rows.append(ActionRow(
                Button(
                    style=color,
                    emoji='❔' if y % 2 == 0 else '❓',
                    custom_id=f'{y*3+1}'
                ),
                Button(
                    style=color,
                    emoji='❓' if y % 2 == 0 else '❔',
                    custom_id=f'{y*3+2}'
                ),Button(
                    style=color,
                    emoji='❔' if y % 2 == 0 else '❓',
                    custom_id=f'{y*3+3}'
                )
            ))
                
        
        # reward_place = random.choice(random.choice(list([x.custom_id for x in row.buttons] for row in rows)))
        components = [row for row in rows]
        components_disabled = [disable_row(row) for row in rows]
        message = await ctx.send(content=quest_message, components=components)

        def check(inter):
            return inter.author == ctx.author

        try:
            inter = await message.wait_for_button_click(check=check, timeout=30)
            inter: Interaction
        except:
            if isinstance(item, Case):
                player.mod_case(item.name, amount)
            elif isinstance(item, Key):
                player.mod_key(item.name, amount)
            elif isinstance(item, int):
                player.balance += item*2
        else:
            if inter.clicked_button.custom_id == str(reward_place):
                if isinstance(item, Case):
                    player.mod_case(item.name, amount * 9)
                elif isinstance(item, Key):
                    player.mod_key(item.name, amount * 9)
                elif isinstance(item, int):
                    player.balance += item*2

                await inter.reply(win_message)
            else:
                print(inter.clicked_button.custom_id, str(reward_place))
                await inter.reply(loss_message)
            
        finally:
            await player.save()
            await message.edit(components=components_disabled)
            

def setup(bot):
    bot.add_cog(GamblingCog(bot))
