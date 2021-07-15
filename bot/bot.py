from discord.colour import Colour
from discord.ext import commands
from dpytools import Color
from pretty_help import PrettyHelp

from modules.constants import owners_ids, DEFAULT_PREFIX

bot = commands.Bot(command_prefix=commands.when_mentioned_or(DEFAULT_PREFIX),
                   case_insensitive=True,
                   help_command=PrettyHelp(color=Colour.random(), no_category="General"),
                   owner_ids=owners_ids)
                   
cogs = {"core"}

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user.name}')
        
async def load_cogs():
  await bot.wait_until_ready()
  for cog in cogs:
    bot.load_extension('bot.cogs.{}'.format(cog))

bot.loop.create_task(load_cogs())