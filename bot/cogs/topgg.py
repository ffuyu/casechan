from discord.ext import tasks

import topgg, os

from ..bot import bot

TOPGG_API = os.environ.get("TOPGG_API")

bot.topggpy = topgg.DBLClient(bot, TOPGG_API)

@tasks.loop(minutes=30)
async def update_stats():
    """This function runs every 30 minutes to automatically update your server count."""
    try:
        await bot.topggpy.post_guild_count()
        print(f"Posted server count ({bot.topggpy.guild_count})")
    except Exception as e:
        print(f"Failed to post server count\n{e.__class__.__name__}: {e}")


update_stats.start()

bot.topgg_webhook = topgg.WebhookManager(bot).dbl_webhook("/dblwebhook", "password")

bot.topgg_webhook.run(5000)


@bot.event
async def on_dbl_vote(data):
    """An event that is called whenever someone votes for the bot on Top.gg."""
    if data["type"] == "test":
        return bot.dispatch("dbl_test", data)

    print(f"Received a vote:\n{data}")


@bot.event
async def on_dbl_test(data):
    """An event that is called whenever someone tests the webhook system for your bot on Top.gg."""
    print(f"Received a test vote:\n{data}")
