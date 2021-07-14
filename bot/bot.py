from discord.ext import commands

bot = commands.Bot(command_prefix='c.')


@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user.name}')
