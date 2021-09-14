from DiscordUtils.Pagination import CustomEmbedPaginator
from discord.colour import Colour
from discord.ext import commands

from dislash import *
from dpytools.embeds import paginate_to_embeds

from bot.bot import inter_client

from modules.database.players import Player
from modules.database.promos import Promo
from modules.database.items import sort_items
from modules.database.players import Player, SafePlayer

class Cog(commands.Cog, name='Context Menu Commands'):
    """Cog containing all context menu commands."""
    def __init__(self, bot):
        self.bot = bot
        print(f'Cog: {self.qualified_name} loaded')

    def cog_unload(self):
        print(f'Cog: {self.qualified_name} unloaded')

    @inter_client.user_command(name="Cases")
    async def user_cases(inter:ContextMenuInteraction):
        """List cases"""
        try:
            if inter.author.bot:
                return await inter.reply("This command cannot be used on bots.", ephemeral=True)
            player = await Player.get(True, member_id=inter.user.id, guild_id=inter.guild_id)
            pages = paginate_to_embeds(description='\n'.join(
                    f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in player.cases.items()),
                    title='{}\'s Cases'.format(inter.user), max_size=130, color=Colour.random())

            paginator = CustomEmbedPaginator(inter, remove_reactions=True)
            if player.cases:
                if len(pages) > 1:
                    paginator.add_reaction('⬅️', "back")
                    paginator.add_reaction('➡️', "next")

                return await paginator.run(pages)
            return await inter.reply(f'**{inter.user}** has no cases to display')
        except:
            pass

    @inter_client.user_command(name="Keys")
    async def user_keys(inter:ContextMenuInteraction):
        """List keys"""
        try:
            if inter.author.bot:
                return await inter.reply("This command cannot be used on bots.", ephemeral=True)
            player = await Player.get(True, member_id=inter.user.id, guild_id=inter.guild_id)
            pages = paginate_to_embeds(description='\n'.join(
                    f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in player.keys.items()),
                    title='{}\'s Keys'.format(inter.user), max_size=130, color=Colour.random())

            paginator = CustomEmbedPaginator(inter, remove_reactions=True)
            if player.keys:
                if len(pages) > 1:
                    paginator.add_reaction('⬅️', "back")
                    paginator.add_reaction('➡️', "next")

                return await paginator.run(pages)
            return await inter.reply(f'**{inter.user}** has no keys to display')
        except:
            pass

    @inter_client.user_command(name="Inventory")
    async def user_inv(inter:ContextMenuInteraction):
        """View inventory"""
        try:
            if inter.author.bot:
                return await inter.reply("This command cannot be used on bots.", ephemeral=True)

            player = await Player.get(True, member_id=inter.user.id, guild_id=inter.guild_id)
            if player.inventory:
                sorted_inventory = sort_items(await player.inv_items())

                pages = paginate_to_embeds(description='\n'.join(['**{}x** {}'.format(player.item_count(item.name), item.name)
                                                                    for item in sorted_inventory]),
                                            title='{}\'s Inventory'.format(inter.user), max_size=400, color=Colour.random())
                paginator = CustomEmbedPaginator(inter, remove_reactions=True)
                if len(pages) > 1:
                    paginator.add_reaction('⬅️', "back")
                    paginator.add_reaction('➡️', "next")

                return await paginator.run(pages)
            return await inter.reply('**{}** has no items to display'.format(inter.user))
        except:
            pass

    @inter_client.message_command(name="Claim")
    async def promo_claim(inter:ContextMenuInteraction):
        """View your inventory"""
        try:
            promo = await Promo.get(code=inter.message.content)
            if promo:
                if not promo.is_expired:
                    if not promo.uses >= promo.max_uses:
                        if not inter.author.id in promo.users:
                            
                            promo.uses += 1
                            promo.users.append(inter.author.id)
                            await promo.save()

                            async with SafePlayer(inter.author.id, inter.guild_id) as player:
                                player.balance += promo.funds
                                
                                await player.save()
                                return await inter.reply(f'Success! You\'ve received **${promo.funds}**', ephemeral=True)

                        return await inter.reply('You have already used this promo code.', ephemeral=True)
                    return await inter.reply('This promo code has reached max uses.', ephemeral=True)
                return await inter.reply('This promo code has expired.', ephemeral=True)
            return await inter.reply('Promo code not found.', ephemeral=True)
        except:
            pass

    
def setup(bot):
    bot.add_cog(Cog(bot))
