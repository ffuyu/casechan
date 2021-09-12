from datetime import datetime as dt
from modules.database.guilds import Guild

from discord import Color
from discord.colour import Colour
from discord.ext import commands
from dislash.interactions.message_components import Button, ButtonStyle
from dpytools import Embed
from humanize import naturaldelta

from dislash import ActionRow

class Cog(commands.Cog, name='Misc'):
    """Miscellaneous commands"""
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @commands.command()
    async def stats(self, ctx):
        """Shows some info on the bot"""
        guilds = self.bot.guilds
        embed = Embed(
            title=f'{self.bot.user.name} stats:',
            description=f'Number of guilds: {len(guilds)}\n'
                        f'Number of users: {len([m for g in guilds for m in g.members])}\n'
                        f'Age: {naturaldelta(dt.utcnow() - self.bot.user.created_at)}'
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx: commands.Context):
        """
        Invite this bot to your server with this command
        """
        invite_url = ("https://discord.com/api/oauth2/authorize?"
                      "client_id=864925623826120714&"
                      "permissions=84032"
                      "&scope=bot%20applications.commands")
        await ctx.send(embed=Embed(
            description=f"Invite **{self.bot.user.name}** to your server with this "
                        f"[link]({invite_url})",
            color=Color.random()
        ))

    @commands.command(aliases=['lat'])
    async def latency(self, ctx):
        """
        Command to display latency in ms.
        Latency is displayed on plain embed in the description field
        """
        ping = await ctx.send(embed=Embed(description=f"Getting latency...", color=Color.purple()))
        latency_ms = round((ping.created_at.timestamp() - ctx.message.created_at.timestamp()) * 1000, 1)
        heartbeat_ms = round(ctx.bot.latency * 1000, 1)
        await ping.edit(content=None,
                        embed=Embed(description=f'Latency: `{latency_ms}ms`\nHeartbeat: `{heartbeat_ms}ms`',
                                    color=Color.purple()))

    @commands.command(aliases=["server"])
    async def support(self, ctx):
        """Join our server and get help by creating support tickets"""
        embed = Embed(
            description="Join our server to get support and engage with other players!",
            color=Colour.random()
        )
        rows = ActionRow(
            Button(
                style=ButtonStyle.link,
                url="https://discord.gg/hjH9AQVmyW",
                label="Join now"
            )
        )

        await ctx.send(embed=embed, components=[rows])

    @commands.command(aliases=["info", "guildinfo"])
    async def serverinfo(self, ctx):
        guild = await Guild.get(True, guild_id=ctx.guild.id)
        embed = Embed(color=Colour.random())
        embed.add_fields(False, **{
            'Global Leaderboards': 'Ineligible' if guild.excluded_from_leaderboards else 'Eligible',
            'Website Visibility': 'Invisible' if guild.excluded_from_web else 'Visible',
            'Cheats': 'Enabled' if guild.server_cheats_enabled else 'Disabled',
            'Status:': 'Modded' if guild.is_excluded else 'Official',
            'Total Worth': f'${await guild.total_worth:.2f}'
        })
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Cog(bot))
