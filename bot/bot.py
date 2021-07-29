import os

from discord.colour import Colour
from discord.ext import commands
from discord.flags import Intents
from pretty_help import PrettyHelp

from modules.constants import owners_ids
from modules.utils import get_command_prefix

intents = Intents.all()
intents.presences = False

bot = commands.Bot(command_prefix=get_command_prefix,
                   case_insensitive=True,
                   intents=intents,
                   help_command=PrettyHelp(color=Colour.random(), no_category="General"),
                   owner_ids=owners_ids)

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user.name}')


async def load_cogs():
    await bot.wait_until_ready()
    for filename in os.listdir('./bot/cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            bot.load_extension(('bot.cogs.' + filename[:-3]))


bot.loop.create_task(load_cogs())
