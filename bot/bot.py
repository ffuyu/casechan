from modules.database.promos import Promo
from modules.database.items import sort_items
from dpytools.embeds import paginate_to_embeds
from modules.database.players import Player, SafePlayer
from modules.constants import owners_ids
from modules.utils import get_command_prefix

import os

from discord.colour import Colour
from discord.ext import commands
from discord.flags import Intents

from pretty_help import PrettyHelp
from dislash import *

from DiscordUtils.Pagination import CustomEmbedPaginator

intents = Intents.all()
intents.presences = False

bot = commands.AutoShardedBot(command_prefix=get_command_prefix,
                   case_insensitive=True,
                   intents=intents,
                   help_command=PrettyHelp(color=Colour.random(), no_category="General"),
                   owner_ids=owners_ids)

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

@inter_client.user_command(name="Keys")
async def user_keys(inter:ContextMenuInteraction):
    """List keys"""
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

@inter_client.user_command(name="Inventory")
async def user_inv(inter:ContextMenuInteraction):
    """View inventory"""
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

@inter_client.message_command(name="Claim")
async def promo_claim(inter:ContextMenuInteraction):
    """View your inventory"""
    promo = await Promo.get(code=inter.message.content)
    if promo:
        if not promo.is_expired:
            if not promo.uses >= promo.max_uses:
                if not inter.author.id in promo.users:
                    
                    promo.uses += 1
                    promo.users.append(inter.author.id)
                    await promo.save()

                    async with SafePlayer(inter.author.id, inter.guild_id) as player:
                        player.balance += promo.funds
                        
                        await player.save()
                        return await inter.reply(f'Success! You\'ve received **${promo.funds}**', ephemeral=True)

                return await inter.reply('You have already used this promo code.', ephemeral=True)
            return await inter.reply('This promo code has reached max uses.', ephemeral=True)
        return await inter.reply('This promo code has expired.', ephemeral=True)
    return await inter.reply('Promo code not found.', ephemeral=True)

bot.loop.create_task(load_cogs())