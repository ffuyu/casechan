"""
Core cog contains the main commands of casechan.
casechan's main purpose is to simulate openings
of CS:GO cases and regarding core features are
as follows:

# Opening containers
# Viewing cases/keys
# Viewing inventory
# Viewing balance
# Viewing leaderboards
"""

import asyncio
from typing import Optional

from DiscordUtils.Pagination import CustomEmbedPaginator
from discord import Member, Embed, Colour, Guild
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.core import guild_only, max_concurrency
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle
from dislash.interactions.slash_interaction import Interaction
from dpytools import Color
from dpytools.embeds import paginate_to_embeds

from modules.cases import Case
from modules.database import Player, Item, engine, GuildConfig
from modules.errors import MissingCase, MissingKey, MissingSpace
from modules.utils import ItemConverter
from modules.utils.case_converter import CaseConverter


def disable_row(row: ActionRow) -> ActionRow:
    for button in row.buttons:
        button.disabled = True

    return row


class CoreCog(commands.Cog, name='Core'):
    """
    This category includes the core commands of the bot
    """

    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @guild_only()
    @max_concurrency(number=1, per=commands.BucketType.member, wait=True)
    @commands.command(name='open')
    async def _open(self, ctx: Context, *, container: Optional[CaseConverter]):
        """
        Opens a case from your cases
        """
        container: Case
        if container:
            player = await Player.get(True, member_id=ctx.author.id, guild_id=ctx.guild.id)
            inv_size = player.inv_items_count()
            # Checks
            if inv_size >= 1000:
                raise MissingSpace('You can\'t open more cases, your inventory is full!')
            if container.name not in player.cases:
                raise MissingCase(f'You are missing {container}.')
            if container.key and container.key not in player.keys:
                raise MissingKey(f'You are missing {container.key}.')

            # Opening animation
            opening_embed = Embed(
                description='**{}**'.format(container),
                color=Colour.random()
            ).set_image(url=container.asset).set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

            message = await ctx.send(embed=opening_embed, reference=ctx.message)
            await asyncio.sleep(6.0)

            # Displaying results
            item, *stats = await container.open()
            player.mod_case(container.name, -1)
            player.mod_key(container.key, -1)
            player.stats['cases']['opened'] += 1
            await player.save()

            # Buttons
            row = ActionRow(
                Button(
                    style=ButtonStyle.grey,
                    label="Claim",
                    custom_id="claim",
                    emoji='📥',
                ),
                Button(
                    style=ButtonStyle.green,
                    label="Sell",
                    custom_id="sell",
                    emoji='💸'
                ),
                Button(
                    style=ButtonStyle.grey,
                    label=f"{inv_size}/1000",
                    custom_id="invsize",
                    disabled=True
                )
            )

            results = Embed(
                description='**{}**'.format(item.name),
                color=item.color
            )
            results.set_image(url='https://community.akamai.steamstatic.com/economy/image/{}'.format(item.icon_url)) \
                .set_footer(text='Float %f | Paint Seed: %d | Price: $%.2f' % (stats[0], stats[1], item.price)) \
                .set_author(name=container, icon_url=container.asset)

            await message.edit(embed=results, components=[row])

            def check(inter):
                return inter.author == ctx.author

            try:
                inter = await message.wait_for_button_click(check=check, timeout=15)
                inter: Interaction
            except:
                player.add_item(item.name, stats)
            else:
                if inter.clicked_button.custom_id == 'claim':
                    player.add_item(item.name, stats)
                    await inter.reply('Claimed **{}** successfully'.format(item.name), ephemeral=True)

                elif inter.clicked_button.custom_id == 'sell':
                    player.balance += (item.price * 0.85)
                    await inter.send('You have sold **{}** and received ${:.2f}'.format(item.name, (item.price * 0.85)),
                                     ephemeral=True)
            finally:
                await player.save()
                return await message.edit(components=[
                    disable_row(row)])  # NOTE custom function used because row.disable_buttons() does not work.

        else:
            return await ctx.send('Not a valid case name!')

    @commands.command(aliases=['keys'])
    async def cases(self, ctx: Context, user: Optional[Member]):
        """List the cases you currently have."""
        user = user or ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)

        if ctx.invoked_with == 'cases':
            if player.cases:
                pages = paginate_to_embeds(description='\n'.join(
                    f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in player.cases.items()),
                                           title='{}\'s Cases'.format(user), max_size=130, color=Colour.random())

                paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
                if len(pages) > 1:
                    paginator.add_reaction('⬅️', "back")
                    paginator.add_reaction('➡️', "next")

                return await paginator.run(pages)

            return await ctx.send(f'**{user}** has no cases to display')  # FIXME (replace with an embed)

        elif ctx.invoked_with == 'keys':
            if player.keys:
                pages = paginate_to_embeds(description='\n'.join(
                    f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in player.keys.items()),
                                           title='{}\'s Keys'.format(user), max_size=150, color=Colour.random())

                paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
                if len(pages) > 1:
                    paginator.add_reaction('⬅️', "back")
                    paginator.add_reaction('➡️', "next")

                return await paginator.run(pages)

        return await ctx.send(f'**{user}** has no cases to display')  # FIXME (replace with an embed)

    @commands.command(aliases=['inv'])
    async def inventory(self, ctx: Context, user: Optional[Member]):
        """View your inventory"""
        user = user or ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        if player.inventory:
            pages = paginate_to_embeds(description='\n'.join(['**{}x** {}'.format(len(player.inventory.get(item)), item)
                                                              for item in player.inventory]),
                                       title='{}\'s Inventory'.format(user), max_size=400, color=Colour.random())
            paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")

            return await paginator.run(pages)
        return await ctx.reply('**{}** has no items to display'.format(user))

    @guild_only()
    @commands.command(aliases=["bal", "b", "networth", "nw"])
    async def balance(self, ctx, user: Optional[Member]):
        """Displays your wallet, inventory and net worth all at once"""
        user = user or ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        inv_total = await player.inv_total()
        await ctx.send(
            embed=Embed(
                color=Colour.random()
            ).set_author(name=user, icon_url=user.avatar_url) \
                .add_field(name="Wallet", value='${:.2f}'.format(player.balance), inline=True)
                .add_field(name="Inventory", value='${:.2f}'.format(inv_total), inline=True)
                .add_field(name="Net worth", value='${:.2f}'.format(player.balance + inv_total), inline=True)
        )

    @guild_only()
    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx: Context, guild: Optional[Guild]):
        """View the inventory worth leaderboard for the server"""
        guild = guild or ctx.guild
        users = await Player.find(guild_id=guild.id)
        users_dictionary = {}
        for user in users:
            member = guild.get_member(user.member_id)
            if member:
                users_dictionary[member.name] = await user.inv_total()

        leaderboard = dict(sorted(users_dictionary.items(), key=lambda item: item[1], reverse=True))

        await ctx.send(
            embed=Embed(
                description='\n'.join(
                    "**{}**: ${:.2f}".format(list(leaderboard.keys())[x], leaderboard[list(leaderboard.keys())[x]]) for
                    x in range(10 if len(list(leaderboard.keys())) >= 10 else len(list(leaderboard.keys())))),
                color=Colour.random()
            ).set_footer(text="Based on inventory worth | Total server inventory worth: ${:.2f}".format(
                sum([x for x in users_dictionary.values()]))).set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        )

    @commands.command()
    async def top(self, ctx):
        """Lists the top 10 most rich servers based on inventory worth"""
        guilds_dictionary = {}
        all_guilds = await engine.find(GuildConfig)
        for guild in all_guilds:
            users = await Player.find(guild_id=guild.guild_id)
            guild_object = self.bot.get_guild(guild.guild_id)
            guilds_dictionary[guild_object.name] = sum([await x.inv_total() for x in users])

        leaderboard = dict(sorted(guilds_dictionary.items(), key=lambda item: item[1], reverse=True))

        embed = Embed(
            title="TOP 10 SERVERS",
            description='\n'.join(
                "**{}**: ${:.2f}".format(list(leaderboard.keys())[x], leaderboard[list(leaderboard.keys())[x]]) for x in
                range(10 if len(list(leaderboard.keys())) >= 10 else len(list(leaderboard.keys())))),
            color=Colour.from_rgb(252, 194, 3)
        ).set_footer(text='Based on inventory worth, not wallets.').set_thumbnail(
            url="https://img.icons8.com/color-glass/48/000000/star.png")

        await ctx.send(embed=embed)

    @commands.command(aliases=['inspect'])
    async def price(self, ctx: Context, *, query: Optional[ItemConverter]):
        """
        Shows item price & asset with specified query
        Args:
            query: the name of the item to search
        """
        if query:
            query: Item
            await ctx.send(embed=query.to_embed(minimal=True if ctx.invoked_with == 'price' else False))
        else:
            await ctx.send(embed=Embed(description='Item not found', color=Color.RED))


def setup(bot):
    bot.add_cog(CoreCog(bot))
