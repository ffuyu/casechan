from discord.colour import Colour
from discord.ext import commands
from pretty_help import PrettyHelp

from modules.constants import owners_ids
from modules.utils import get_command_prefix

bot = commands.Bot(command_prefix=get_command_prefix,
                   case_insensitive=True,
                   help_command=PrettyHelp(color=Colour.random(), no_category="General"),
                   owner_ids=owners_ids)

cogs = {'core', 'configuration'}


@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user.name}')


async def load_cogs():
    await bot.wait_until_ready()
    for cog in cogs:
        bot.load_extension('bot.cogs.{}'.format(cog))


bot.loop.create_task(load_cogs())
