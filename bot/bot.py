from modules.database.promos import Promo
from modules.database.items import sort_items
from dpytools.embeds import paginate_to_embeds
from modules.database.players import Player, SafePlayer
from modules.config import config, OWNERS_IDS
from modules.utils import get_command_prefix
from modules.database import Item, engine

import os
import logging

from discord.colour import Colour
from discord.ext import commands
from discord.flags import Intents

from pretty_help import PrettyHelp
from dislash import *
from DiscordUtils.Pagination import CustomEmbedPaginator


intents = Intents.default()
intents.members = True

log = logging.getLogger(__name__)

bot = commands.AutoShardedBot(command_prefix=get_command_prefix,
                              case_insensitive=True,
                              intents=intents,
                              help_command=PrettyHelp(
                                  color=Colour.random(), no_category="General"),
                              owner_ids=OWNERS_IDS)

SlashClient(bot)
inter_client = InteractionClient(bot)


@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user.name}')


async def load_cogs():
    await bot.wait_until_ready()
    for filename in os.listdir('./bot/cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            bot.load_extension(('bot.cogs.' + filename[:-3]))

@inter_client.user_command(name="Cases")
async def user_cases(inter:ContextMenuInteraction):
    """List cases"""
    try:
        if inter.author.bot:
            return await inter.reply("This command cannot be used on bots.", ephemeral=True)
        player = await Player.get(True, member_id=inter.user.id, guild_id=inter.guild_id)
        pages = paginate_to_embeds(description='\n'.join(
                f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in player.cases.items()),
                title='{}\'s Cases'.format(inter.user), max_size=130, color=Colour.random())

        paginator = CustomEmbedPaginator(inter, remove_reactions=True)
        if player.cases:
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")

            return await paginator.run(pages)
        return await inter.reply(f'**{inter.user}** has no cases to display')
    except:
        pass

@inter_client.user_command(name="Keys")
async def user_keys(inter:ContextMenuInteraction):
    """List keys"""
    try:
        if inter.author.bot:
            return await inter.reply("This command cannot be used on bots.", ephemeral=True)
        player = await Player.get(True, member_id=inter.user.id, guild_id=inter.guild_id)
        pages = paginate_to_embeds(description='\n'.join(
                f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in player.keys.items()),
                title='{}\'s Keys'.format(inter.user), max_size=130, color=Colour.random())

        paginator = CustomEmbedPaginator(inter, remove_reactions=True)
        if player.keys:
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")

            return await paginator.run(pages)
        return await inter.reply(f'**{inter.user}** has no keys to display')
    except:
        pass

@inter_client.user_command(name="Inventory")
async def user_inv(inter:ContextMenuInteraction):
    """View inventory"""
    try:
        if inter.author.bot:
            return await inter.reply("This command cannot be used on bots.", ephemeral=True)

        player = await Player.get(True, member_id=inter.user.id, guild_id=inter.guild_id)
        if player.inventory:
            sorted_inventory = sort_items(await player.inv_items())

            pages = paginate_to_embeds(description='\n'.join(['**{}x** {}'.format(player.item_count(item.name), item.name)
                                                                for item in sorted_inventory]),
                                        title='{}\'s Inventory'.format(inter.user), max_size=400, color=Colour.random())
            paginator = CustomEmbedPaginator(inter, remove_reactions=True)
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")

            return await paginator.run(pages)
        return await inter.reply('**{}** has no items to display'.format(inter.user))
    except:
        pass

@inter_client.message_command(name="Claim")
async def promo_claim(inter:ContextMenuInteraction):
    """View your inventory"""
    try:
        promo = await Promo.get(code=inter.message.content)
        if promo:
            temp = await Player.get(True, member_id=inter.author.id, guild_id=inter.guild.id)
            if promo.eligible_for(temp):
                promo.uses += 1
                promo.users.append(inter.author.id)
                await promo.save()

                # used promo before waiting for safe player for security and prevent abuse / stealing code

                async with SafePlayer(inter.author.id, inter.guild.id) as player:
                    player.balance += promo.funds
                    await player.save()
                    await inter.send(f'Success! You\'ve received **${promo.funds}**', ephemeral=True)
            else:
                await inter.send('You are ineligible for this promo code.', ephemeral=True)

            return
        await inter.send('Promo code not found.', ephemeral=True)
    except:
        pass

async def check_items_col():
    if not await engine.find_one(Item):
        log.warning(
            'There are no items in the items collection | Case openings will fail!')


bot.loop.create_task(load_cogs())
bot.loop.create_task(check_items_col())
