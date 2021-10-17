"""
TopGGCog automatically POST's the server count to top.gg
and listens for upvotes coming from top.gg to reward the voters
"""

from datetime import datetime
from discord.ext import tasks, commands

import topgg, os

from ..bot import bot

from modules.database.users import UserData
from modules.config import config

TOPGG_API = os.environ.get("TOPGG_API")
WEBHOOK = os.environ.get("WEBHOOK")
DEBUG = config.get('debug') == True

bot.topggpy = topgg.DBLClient(bot, TOPGG_API, autopost=DEBUG, post_shard_count=DEBUG)

bot.topgg_webhook = topgg.WebhookManager(bot).dbl_webhook("/upvote", WEBHOOK)
bot.topgg_webhook.run(5000)

class TopGGCog(commands.Cog):
    @bot.event
    async def on_autopost_success():
        print(
            f"Posted server count ({bot.topggpy.guild_count}), shard count ({bot.shard_count})"
        )


    @bot.event
    async def on_dbl_vote(data):
        """An event that is called whenever someone votes for the bot on Top.gg."""
        if data["type"] == "test":
            return bot.dispatch("dbl_test", data)

        print(f"Received a vote:\n{data}")

        voter = await UserData.get(True, user_id=int(data.get('user', '0')))

        voter.total_votes += 1
        voter.last_voted = datetime.utcnow()
        
        await voter.save()

    @bot.event
    async def on_dbl_test(data):
        """An event that is called whenever someone tests the webhook system for your bot on Top.gg."""
        print(f"Received a test vote:\n{data}")



def setup(bot):
    bot.add_cog(TopGGCog(bot))
