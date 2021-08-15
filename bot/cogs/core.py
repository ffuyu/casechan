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
from os import name

from discord.abc import User
from modules.database.items import Item, sort_items
from modules.database.players import Player
from typing import Optional

from DiscordUtils.Pagination import CustomEmbedPaginator
from discord import Member, Colour, PartialEmoji
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands.core import guild_only, max_concurrency
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle
from dislash import *
from dpytools.embeds import Embed
from dpytools.embeds import paginate_to_embeds

from modules.cases import Case, all_cases
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

    @slash_commands.guild_only()
    @max_concurrency(number=1, per=commands.BucketType.member, wait=True)
    @slash_commands.slash_command(name="open", guild_ids = [876199559729147914], description="Opens the specified case", options=[
        Option(
            name="container",
            description="Case to open",
            type=Type.STRING,
            required=True
        ),
        Option(
            name="amount",
            description="Amount of cases to open",
            type=Type.INTEGER,
            required=False
        )
    ])
    async def _open(self, inter, amount: Optional[int] = 1, *, container: str):
        """
        Opens a case from your cases
        """
        container = await CaseConverter().convert(inter, container)
        container: Case
        if not container:
            return await inter.reply('Not a valid case name!', ephemeral=True)

        async with SafePlayer(inter.author.id, inter.guild.id) as player:
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
            ).set_author(name=inter.author, icon_url=inter.author.avatar_url)

            message = await inter.reply(embed=opening_embed)
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
                       emoji=PartialEmoji(name='💸'),
                       disabled=player.trade_banned),
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
                return inter_.author == inter.author

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
                    user = await UserData.get(True, user_id=inter.author.id)
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

    @guild_only()
    @slash_commands.cooldown(10, 60, BucketType.member)
    @slash_commands.slash_command(name="cases", description="Lists the cases you currently have", guild_ids=[876199559729147914], options=[
        Option(
            name="user",
            description="User to retrieve the cases from",
            type=Type.USER,
            required=False
        ),

    ])
    async def cases(self, inter, user:Optional[User]=None):
        """List the cases you currently have."""
        user = user if user and not user.bot else inter.author
        player = await Player.get(True, member_id=user.id, guild_id=inter.guild.id)

        if player.cases:
            pages = paginate_to_embeds(description='\n'.join(
                f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in player.cases.items()),
                title='{}\'s Cases'.format(user), max_size=130, color=Colour.random())

            paginator = CustomEmbedPaginator(inter, remove_reactions=True)
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")

            await paginator.run(pages)

        await inter.reply(f'**{user}** has no cases to display', ephemeral=True)

    @guild_only()
    @slash_commands.cooldown(10, 60, BucketType.member)
    @slash_commands.slash_command(name="keys", description="Lists the keys you currently have", guild_ids=[876199559729147914], options=[
        Option(
            name="user",
            description="User to retrieve the keys from",
            type=Type.USER,
            required=False
        ),

    ])
    async def keys(self, inter, user:Optional[User]=None):
        """List the keys you currently have."""
        user = user if user and not user.bot else inter.author
        player = await Player.get(True, member_id=user.id, guild_id=inter.guild.id)

        if player.keys:
            pages = paginate_to_embeds(description='\n'.join(
                f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in player.keys.items()),
                title='{}\'s Keys'.format(user), max_size=130, color=Colour.random())

            paginator = CustomEmbedPaginator(inter, remove_reactions=True)
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")

            await paginator.run(pages)

        await inter.reply(f'**{user}** has no keys to display', ephemeral=True)


    @guild_only()
    @slash_commands.cooldown(10, 30, BucketType.member)
    @slash_commands.slash_command(name="inventory", description="Displays your inventory", guild_ids=[876199559729147914], options=[
        Option(
            name="user",
            description="User to retrieve the inventory from",
            type=Type.USER,
            required=False
        ),

    ])
    async def inventory(self, inter, *, user: Optional[User]=None):
        """View your inventory"""
        user = user if user and not user.bot else inter.author
        player = await Player.get(True, member_id=user.id, guild_id=inter.guild.id)
        if player.inventory:
            sorted_inventory = sort_items(await player.inv_items())

            pages = paginate_to_embeds(description='\n'.join(['**{}x** {}'.format(player.item_count(item.name), item.name)
                                                              for item in sorted_inventory]),
                                       title='{}\'s Inventory'.format(user), max_size=400, color=Colour.random())
            paginator = CustomEmbedPaginator(inter, remove_reactions=True)
            if len(pages) > 1:
                paginator.add_reaction('⬅️', "back")
                paginator.add_reaction('➡️', "next")
    
            await paginator.run(pages)
        await inter.reply('**{}** has no items to display'.format(user), ephemeral=True)

    @guild_only()
    @slash_commands.cooldown(10, 30, BucketType.member)
    @slash_commands.slash_command(name="balance", description="Displays your wallet, inventory worth and net worth", guild_ids=[876199559729147914], options=[
        Option(
            name="user",
            description="User to retrieve the balance from",
            type=Type.USER,
            required=False
        ),

    ])
    async def balance(self, inter, *, user: Optional[User]=None):
        """Displays your wallet, inventory and net worth all at once"""
        user = user if user and not user.bot else inter.author
        player = await Player.get(True, member_id=user.id, guild_id=inter.guild.id)
        inv_total = await player.inv_total()
        await inter.send(
            embed=Embed(
                color=Colour.random()
            ).set_author(name=user, icon_url=user.avatar_url) \
                .add_field(name="Wallet", value='${:.2f}'.format(player.balance), inline=True)
                .add_field(name="Inventory", value='${:.2f}'.format(inv_total), inline=True)
                .add_field(name="Net worth", value='${:.2f}'.format(player.balance + inv_total), inline=True)
        )


def setup(bot):
    bot.add_cog(CoreCog(bot))
