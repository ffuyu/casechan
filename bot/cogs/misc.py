import asyncio
from bot.cogs.core import disable_row
from datetime import datetime as dt, timedelta
from modules.emojis import Emojis
from modules.database import engine
from modules.database.players import Player
from typing import Optional
from discord.ext.commands.errors import CommandError

from dislash.application_commands.errors import MissingPermissions
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

    @commands.command(aliases=["info"])
    async def serverinfo(self, ctx):
        """
        Displays various information about the server
        """
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

    @commands.command()
    async def cheats(self, ctx, action:Optional[bool]):
        """
        Command for server owners to toggle cheats
        """
        guild = await Guild.get(True, guild_id=ctx.guild.id)
        if action is None:
            await ctx.send(f'Your server has cheats {"enabled" if guild.server_cheats_enabled else "disabled"}. Re-run this command with `on or off` to change.')
        else:
            if ctx.author != ctx.guild.owner: raise CommandError(f'This setting can only be changed by the server owner, **{ctx.guild.owner}**')
            if action is True:
                if guild.server_cheats_enabled: return await ctx.send('You have cheats enabled!')
                confirmation_embed = Embed(
                    title = "CONFIRM",
                    description = 
                    """
                    Enabling server cheats will give your server its own space on casechan at the cost of being removed from global leaderboards and anything that involves the official servers.
                    Enabling server cheats will not reset progress your players have made in your server, however, if you want to turn cheats off in the future, all your progress will reset.
                    Once the cheats are enabled, server administrators will be allowed to give cases (including keys) and create promo codes which will let you shape your own economy. 
                    Server administrators will also have the permissions to apply trade restrictions and remove them to any player in this server.
                    """,
                    color = Colour.red()
                )
                row = ActionRow(Button(style=ButtonStyle.red, label='Proceed'), Button(style=ButtonStyle.gray, label='Nevermind'))
                con = await ctx.send(embed=confirmation_embed, components=[row])
                def check(inter): return inter.author == ctx.author and ctx.author == ctx.guild.owner 
                try: inter = await con.wait_for_button_click(check=check, timeout=90)
                except asyncio.TimeoutError: return await con.edit(components=[disable_row(row)])
                else: 
                    if inter.clicked_button.label == 'Proceed':
                        guild.server_cheats_enabled = True
                        await guild.save()
                        await ctx.send(f'You\'ve successfully enabled cheats for **{ctx.guild}**')
                    else:
                        pass
                finally: 
                    await con.delete()

            elif action is False:
                if not guild.server_cheats_enabled: return await ctx.send('You don\'t have cheats enabled!')
                players_from_guild = await engine.find(Player, Player.guild_id==ctx.guild.id)
                confirmation_embed = Embed(
                    title = "CONFIRM",
                    description = 
                    f"""
                    You are about to disable cheats for **{ctx.guild}**! If you continue, **{len(players_from_guild)}** players, a total of **${await guild.total_worth:.2f}** and everything else will reset.
                    """,
                    color = Colour.red()
                )
                row = ActionRow(Button(style=ButtonStyle.red, label='Proceed'), Button(style=ButtonStyle.gray, label='Nevermind'))
                con = await ctx.send(embed=confirmation_embed, components=[row])
                def check(inter): return inter.author == ctx.author and ctx.author == ctx.guild.owner 
                try: inter = await con.wait_for_button_click(check=check, timeout=90)
                except asyncio.TimeoutError: return await con.edit(components=[disable_row(row)])
                else: 
                    if inter.clicked_button.label == 'Proceed':
                        loading = await ctx.send(f'{Emojis.SUCCESS.value} Cheats disabled successfully. Resetting server...')
                        guild.server_cheats_enabled = False
                        await guild.save()
                        for player in players_from_guild:
                            player.inventory = {}
                            player.cases = {}
                            player.keys = {}
                            player.balance = 0.00
                            player.hourly = dt.utcnow() - timedelta(hours=1)
                            player.daily = dt.utcnow() - timedelta(days=1)
                            player.weekly = dt.utcnow() - timedelta(weeks=1)
                            player.streak = 0
                            player.trade_banned = False
                            await player.save()

                        await loading.delete()
                        await ctx.send(f'You\'ve successfully disabled cheats for **{ctx.guild}**')
                    else: pass
                finally: await con.delete()
def setup(bot):
    bot.add_cog(Cog(bot))
