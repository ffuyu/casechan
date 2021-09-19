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


async def check_items_col():
    if not await engine.find_one(Item):
        log.warning(
            'There are no items in the items collection | Case openings will fail!')


bot.loop.create_task(load_cogs())
bot.loop.create_task(check_items_col())
