from discord.ext import commands


class Cog(commands.Cog, name='Cog Cookie Cutter'):
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')


def setup(bot):
    bot.add_cog(Cog(bot))