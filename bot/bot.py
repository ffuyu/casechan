from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned_or('c.'), case_insensitive=True, help_command=None, owner_ids={717747572076314745})
cogs = {"core"}

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user.name}')
        
async def load_cogs():
  await bot.wait_until_ready()
  for cog in cogs:
    bot.load_extension('bot.cogs.{}'.format(cog))

bot.loop.create_task(load_cogs())