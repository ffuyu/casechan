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
from modules.database.items import sort_items
from modules.database.players import Player
from typing import Optional

from DiscordUtils.Pagination import CustomEmbedPaginator
from discord import Member, Colour, PartialEmoji
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle
from dpytools.embeds import Embed
from dpytools.embeds import paginate_to_embeds

from modules.cases import Case
from modules.database import Player, SafePlayer
from modules.database.users import UserData
from modules.errors import MissingCase, MissingKey, MissingSpace
from modules.utils.case_converter import CaseConverter

from etc.emojis import emojis

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
    async def _open(self, ctx: Context, amount: Optional[int] = 1, *, container: Optional[CaseConverter]):
        """
        Opens a case from your cases
        """
        container: Case
        if not container:
            return await ctx.send('Not a valid case name!')

        async with SafePlayer(ctx.author.id, ctx.guild.id) as player:
            amount = amount if amount > 0 else 1
            inv_size = player.inv_items_count()

            # checks
            if inv_size > 1000 - amount:
                raise MissingSpace('You can\'t open more cases, your inventory is full!')
            if amount > player.cases.get(container.name, 0):
                raise MissingCase(f'You are missing '
                                  f'{amount - player.cases.get(container.name, 0)} {container}.')
            if container.key and amount > player.keys.get(container.key, 0):
                raise MissingKey(f'You are missing '
                                 f'{amount - player.keys.get(container.key, 0)} {container.key}.')

            # Opening embed
            opening_embed = Embed(
                description=f'**<a:casechanloading:874960632187879465> {container}**',
                color=Colour.random(),
                image=container.asset
            ).set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

            message = await ctx.send(embed=opening_embed, reference=ctx.message)
            await asyncio.sleep(6.0)

            # Updating Player
            player.mod_case(container.name, -amount)
            player.mod_key(container.key, -amount)
            player.stats['cases']['opened'] += amount

            # Opening cases
            items = [await container.open() for _ in range(amount)]
            item_objects = [k for k, _, _ in items]

            # Buttons
            row = ActionRow(
                Button(style=ButtonStyle.grey,
                       label="Claim" if amount == 1 else "Claim all",
                       custom_id="claim",
                       emoji=PartialEmoji(name='📥')),
                Button(style=ButtonStyle.green,
                       label="Sell" if amount == 1 else "Sell all",
                       custom_id="sell",
                       emoji=PartialEmoji(name='💸')),
                Button(style=ButtonStyle.grey,
                       label=f"{inv_size + amount}/1000",
                       custom_id="invsize",
                       disabled=True)
            )

            # Displaying results (Bulk)
            if amount != 1:
                results = Embed(
                    color=Colour.random()
                ).set_author(name=container.name, icon_url=container.asset)

                if len(items) > 5:
                    worth = sum([x.price for x in item_objects])
                    results.description = (f"You have opened **{amount}x {container.name}**. "
                                           f"Total items worth: **${worth:.2f}**")
                else:
                    desc = f"You have opened **{amount}x {container.name}** " \
                           f"and received the following items: \n\n"
                    desc += '\n'.join([f'{emojis.get(item.rarity)} {item.name} ${item.price}' for item in item_objects])
                    results.description = desc

                await message.edit(embed=results, components=[row])

            # Displaying results (Single)
            else:
                item, *stats = items[0]
                results = Embed(
                    description=f'{emojis.get(item.rarity)} **{item.name}**',
                    color=item.color,
                    image=f'https://community.akamai.steamstatic.com/economy/image/{item.icon_url}'
                ).set_footer(text='Float %f | Paint Seed: %d | Price: $%.2f' % (stats[0], stats[1], item.price)) \
                    .set_author(name=container, icon_url=container.asset)

                await message.edit(embed=results, components=[row])

            def check(inter_):
                return inter_.author == ctx.author

            try:
                inter = await message.wait_for_button_click(check=check, timeout=30)
                # inter: Interaction
            except asyncio.TimeoutError:
                if amount != 1:
                    for item in items:
                        i, *s = item
                        player.add_item(i.name, s)
                else:
                    player.add_item(item.name, stats)
            else:
                if inter.clicked_button.custom_id == 'claim':
                    if amount != 1:
                        for item in items:
                            i, *s = item
                            player.add_item(i.name, s)
                        await inter.reply(f'Claimed **{len(item_objects)}** items successfully', ephemeral=True)
                    else:
                        player.add_item(item.name, stats)
                        await inter.reply(f'Claimed **{item.name}** successfully', ephemeral=True)

                elif inter.clicked_button.custom_id == 'sell':
                    user = await UserData.get(True, user_id=ctx.author.id)
                    fees = user.fees
                    total_received = 0.0
                    if amount != 1:
                        for item in item_objects:
                            total_received += (item.price * fees)
                    else:
                        total_received += (item.price * fees)
                    await inter.send('You have sold **{}** and received ${:.2f}'.format(
                        item.name if amount == 1 else f'{len(items)} items', total_received),
                        ephemeral=True)
                    player.balance += total_received
            finally:
                await player.save()
                # NOTE custom function used because row.disable_buttons() does not work.
                return await message.edit(components=[disable_row(row)])


    @commands.cooldown(10, 60, BucketType.member)
    @commands.command(aliases=['keys'])
    async def cases(self, ctx: Context, *, user: Optional[Member]):
        """List the cases you currently have."""
        user = user if user and not user.bot else ctx.author
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

        return await ctx.send(
            f'**{user}** has no {"cases" if ctx.invoked_with == "cases" else "keys"} to display')  # FIXME (replace with an embed)

    @commands.cooldown(10, 30, BucketType.member)
    @commands.command(aliases=['inv'])
    async def inventory(self, ctx: Context, *, user: Optional[Member]):
        """View your inventory"""
        user = user if user and not user.bot else ctx.author
        player = await Player.get(True, member_id=user.id, guild_id=ctx.guild.id)
        if player.inventory:
            sorted_inventory = sort_items(await player.inv_items())

            pages = paginate_to_embeds(description='\n'.join(['**{}x** {}'.format(player.item_count(item.name), item.name)
                                                              for item in sorted_inventory]),
                                       title='{}\'s Inventory'.format(user), max_size=400, color=Colour.random())
            paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")

            return await paginator.run(pages)
        return await ctx.reply('**{}** has no items to display'.format(user))

    @guild_only()
    @commands.cooldown(10, 30, BucketType.member)
    @commands.command(aliases=["bal", "b", "networth", "nw"])
    async def balance(self, ctx, *, user: Optional[Member]):
        """Displays your wallet, inventory and net worth all at once"""
        user = user if user and not user.bot else ctx.author
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

    


def setup(bot):
    bot.add_cog(CoreCog(bot))
