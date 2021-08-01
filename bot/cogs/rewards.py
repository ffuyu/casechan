import datetime, random

from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import max_concurrency

from modules.database.players import Player
from modules.cases import Case, all_cases
from modules.errors import DailyError, WeeklyError, HourlyError

class RewardsCog(commands.Cog, name='Rewards'):
    """
    Contains hourly, daily and weekly commands
    """
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')


    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def hourly(self, ctx:Context):
        """
        Claim your hourly rewards
        """
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        # player.daily = datetime.datetime.now() - datetime.timedelta(days=5)
        if (datetime.datetime.now() - player.hourly) > datetime.timedelta(hours=1):

            player.hourly = datetime.datetime.now()
            amount = random.randint(4,7) \
                if ctx.author.created_at - datetime.datetime.now() < datetime.timedelta(weeks=1) else 1
            
            for _ in range(amount):
                case = Case(random.choice([x for x in all_cases]))
                player.mod_case(case.name, 1)
                player.mod_key(case.key, 1)
            await player.save()
            
            return await ctx.send(f'Claimed **{amount}x** cases from hourly rewards.')

        raise HourlyError(f'You have to wait {datetime.timedelta(seconds=(player.hourly - datetime.datetime.now()).seconds)} to claim your next hourly rewards.')

    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def daily(self, ctx:Context):
        """
        Claim your daily rewards
        """
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        # player.daily = datetime.datetime.now() - datetime.timedelta(days=5)
        if (datetime.datetime.now() - player.daily) > datetime.timedelta(days=1):
            if (datetime.datetime.now() - player.daily) > datetime.timedelta(days=2):
                player.streak = 0

            player.daily = datetime.datetime.now()
            player.streak += 1
            amount = random.randint(player.streak, player.streak+10) \
                if ctx.author.created_at - datetime.datetime.now() < datetime.timedelta(days=7) else 2
            
            for _ in range(amount):
                case = Case(random.choice([x for x in all_cases]))
                player.mod_case(case.name, 1)
                player.mod_key(case.key, 1)
            await player.save()
            
            return await ctx.send(f'Claimed **{amount}x** cases from daily rewards.')

        raise DailyError(f'You have to wait {datetime.timedelta(seconds=(player.daily - datetime.datetime.now()).seconds)} to claim your next daily rewards.')

    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def weekly(self, ctx:Context):
        """
        Claim your weekly rewards
        """
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        if datetime.datetime.now() - ctx.author.created_at < datetime.timedelta(weeks=1):
            print(ctx.author.created_at - datetime.datetime.now())
            raise WeeklyError('Your account is ineligible to claim weekly rewards.')

        if (datetime.datetime.now() - player.weekly) > datetime.timedelta(weeks=1):

            player.weekly = datetime.datetime.now()
            range_ = random.choices([(25, 50), (50, 100), (100, 250), (250, 500), (500, 1000)], weights=[50, 25, 20, 4.9, 0.1], k=1)[0]
            amount = random.randint(range_[0], range_[1])
            
            for _ in range(amount):
                case = Case(random.choice([x for x in all_cases]))
                player.mod_case(case.name, 1)
                player.mod_key(case.key, 1)
            await player.save()
            
            return await ctx.send(f'Claimed **{amount}x** cases from weekly rewards.')

        raise HourlyError(f'You have to wait {datetime.timedelta(seconds=(player.weekly - datetime.datetime.now()).seconds)} to claim your next weekly rewards.')

def setup(bot):
    bot.add_cog(RewardsCog(bot))
