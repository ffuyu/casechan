from DiscordUtils.Pagination import CustomEmbedPaginator
from discord.colour import Colour
from discord.ext.commands.context import Context
from dpytools.embeds import paginate_to_embeds

async def dict_paginator(title:str, ctx:Context, items:dict):
    pages = paginate_to_embeds(description='\n'.join(
        f'**{v}x** {k[:20] + "..." if len(k) > 22 else k}' for k, v in items.items()),
        title=title, max_size=150, color=Colour.random())

    paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
    if len(pages) > 1:
        paginator.add_reaction('⬅️', "back")
        paginator.add_reaction('➡️', "next")

    return await paginator.run(pages)

async def paginator(title:str, ctx, items:list):
    pages = paginate_to_embeds(description='\n'.join(
        f'{item.name[:20] + "..." if len(item.name) > 22 else item.name}' for item in items),
        title=title, max_size=150, color=Colour.random())

    paginator = CustomEmbedPaginator(ctx, remove_reactions=True)
    if len(pages) > 1:
        paginator.add_reaction('⬅️', "back")
        paginator.add_reaction('➡️', "next")

    return await paginator.run(pages)