from discord.ext import tasks, commands

import topgg, os

from ..bot import bot

TOPGG_API = os.environ.get("TOPGG_API")

bot.topggpy = topgg.DBLClient(bot, TOPGG_API, autopost=True, post_shard_count=True)

bot.topgg_webhook = topgg.WebhookManager(bot).dbl_webhook("/dblwebhook", "password")
bot.topgg_webhook.run(5000)

class TopGGCog(commands.Cog):
    @bot.event
    async def on_autopost_success(self):
        print(
            f"Posted server count ({bot.topggpy.guild_count}), shard count ({bot.shard_count})"
        )


    @bot.event
    async def on_dbl_vote(self, data):
        """An event that is called whenever someone votes for the bot on Top.gg."""
        if data["type"] == "test":
            return bot.dispatch("dbl_test", data)

        print(f"Received a vote:\n{data}")


    @bot.event
    async def on_dbl_test(self, data):
        """An event that is called whenever someone tests the webhook system for your bot on Top.gg."""
        print(f"Received a test vote:\n{data}")



def setup(bot):
    bot.add_cog(TopGGCog(bot))
