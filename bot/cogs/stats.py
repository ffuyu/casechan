from discord.ext import commands
from modules.config import config
import statcord


class StatcordPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.key = "statcord.com-xAFUE1mTcPYIxaEC72sD"
        self.api = statcord.Client(self.bot,self.key)
        if config.get('DEBUG') == False:
            self.api.start_loop()


    @commands.Cog.listener()
    async def on_command(self,ctx):
        self.api.command_run(ctx)


def setup(bot):
    bot.add_cog(StatcordPost(bot))