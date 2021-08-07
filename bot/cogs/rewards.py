import datetime
import random

from discord import Embed
from discord.colour import Colour
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import max_concurrency
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle
from dislash.interactions.slash_interaction import Interaction
from humanize import naturaldelta

from modules.cases import Case, all_cases
from modules.database.players import Player
from modules.errors import DailyError, WeeklyError, HourlyError


async def _reward_cases(player, to_give):
    given = 0
    while given < to_give:
        case = Case(random.choice([*all_cases]))
        n = random.randint(0, to_give - given)
        player.mod_case(case.name, n)
        player.mod_key(case.key, n)
        given += n
    await player.save()


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
    async def hourly(self, ctx: Context):
        """
        Claim your hourly rewards
        """
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        # player.daily = datetime.datetime.utcnow() - datetime.timedelta(days=5)
        if (datetime.datetime.utcnow() - player.hourly) > datetime.timedelta(hours=1):
            player.hourly = datetime.datetime.utcnow()
            amount = random.randint(4, 7) \
                if ctx.author.created_at - datetime.datetime.utcnow() < datetime.timedelta(weeks=1) else 1

            await _reward_cases(player, amount)

            return await ctx.send(f'Claimed **{amount}x** cases from hourly rewards.')

        remaining = player.hourly + datetime.timedelta(hours=1) - datetime.datetime.utcnow()

        raise HourlyError(f'You have to wait {naturaldelta(remaining)} to claim your next hourly rewards.')

    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def daily(self, ctx: Context):
        """
        Claim your daily rewards
        """
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        # player.daily = datetime.datetime.utcnow() - datetime.timedelta(days=5)
        if (datetime.datetime.utcnow() - player.daily) > datetime.timedelta(days=1):
            if (datetime.datetime.utcnow() - player.daily) > datetime.timedelta(days=2):
                player.streak = 0

            player.daily = datetime.datetime.utcnow()
            player.streak += 1
            amount = random.randint(player.streak, player.streak + 10) \
                if ctx.author.created_at - datetime.datetime.utcnow() < datetime.timedelta(days=7) else 2

            await _reward_cases(player, amount)

            return await ctx.send(f'Claimed **{amount}x** cases from daily rewards.')

        remaining = player.daily + datetime.timedelta(days=1) - datetime.datetime.utcnow()

        raise DailyError(f'You have to wait {naturaldelta(remaining)} to claim your next daily rewards.')

    @max_concurrency(1, BucketType.member, wait=False)
    @commands.command()
    async def weekly(self, ctx: Context):
        """
        Claim your weekly rewards
        """
        player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
        if datetime.datetime.utcnow() - ctx.author.created_at < datetime.timedelta(weeks=1):
            raise WeeklyError('Your account is ineligible to claim weekly rewards.')

        if (datetime.datetime.utcnow() - player.weekly) > datetime.timedelta(weeks=1):
            player.weekly = datetime.datetime.utcnow()
            range_ = \
                random.choices([(25, 50), (50, 100), (100, 250), (250, 500), (500, 1000)],
                               weights=[50, 25, 20, 4.9, 0.1],
                               k=1)[0]
            amount = random.randint(range_[0], range_[1])

            await _reward_cases(player, amount)

            return await ctx.send(f'Claimed **{amount}x** cases from weekly rewards.')

        remaining = player.weekly + datetime.timedelta(weeks=1) - datetime.datetime.utcnow()

        raise WeeklyError(f'You have to wait {naturaldelta(remaining)} to claim your next weekly rewards.')

    @commands.command(aliases=["upvote"])
    async def vote(self, ctx):
        """Vote for casechan and get perks"""
        embed = Embed(
            description="Vote for **casechan** and reduce your selling fees down to 5% for 12 hours!",
            color=Colour.random()
        )
        rows = ActionRow(
            Button(
                style=ButtonStyle.link,
                url="https://top.gg/bot/864925623826120714/vote",
                label="Vote now"
            )
        )

        message = await ctx.send(embed=embed, components=[rows])

        def check(inter):
            return inter.id == message.id

        try:
            inter = await message.wait_for_button_click(check=check, timeout=60)
            inter: Interaction
        except:
            await ctx.message.delete()
        else:
            if inter.clicked_button.custom_id == 'vote':
                await inter.reply('Your perks will be granted as soon as you vote, thank you for voting! :heart:',
                                  ephemeral=True)


def setup(bot):
    bot.add_cog(RewardsCog(bot))
