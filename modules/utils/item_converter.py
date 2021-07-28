"""
Cases covered by converter:
    User inputs the complete name
    User inputs complete name without star
    User inputs name with abbreviations
"""
import logging
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import List

from discord.ext.commands import Converter, Context

from modules.database import Item

__all__ = (
    'ItemConverter',
)

log = logging.getLogger(__name__)

_replacements = {
    "kato": "katowice",
    "katow": "katowice",
    "fn": "factory new",
    "mw": "minimal wear",
    "ft": "field tested",
    "ww": "well worn",
    "bs": "battle-scarred",
    "so": "souvenir",
    "st": "stattrak",
    "bfk": "butterfly knife",
    "ibp": "ibuypower",
    "ruby": "doppler",
    "sapphire": "doppler",
    "ak": "ak 47",
    "scout": "ssg08",
    "deagle": "desert eagle",
    "kara": "karambit",
    "navi": "natus vincere",
    "cz": "cz75-auto",
}

_names_cache = []


class ItemConverter(Converter):

    @staticmethod
    def _replace_abbr(string):
        out = string.split()
        for word in out:
            w = word
            for k, v in _replacements.items():
                w = w.replace(k, v)
            out[out.index(word)] = w
        return ' '.join(out)

    @staticmethod
    def _clean_str(string):
        new_string = (
            string
                .lower()
                .replace('★', '')
                .replace('StatTrak™', '')
                .replace(' |', '')
                .replace('(', '')
                .replace(')', '')
                .strip()
        )
        return new_string

    def _item_names(self, item_cache: List[Item]):
        return {self._clean_str(item.name): item for item in item_cache}

    async def convert(self, ctx: Context, argument: str):
        global _names_cache
        target = None

        await ctx.channel.trigger_typing()
        argument = self._clean_str(argument)
        item_cache = await Item.item_cache()
        if not _names_cache:
            log.info('Refreshing names cache...')
            with ProcessPoolExecutor() as pool:
                _names_cache = await ctx.bot.loop.run_in_executor(pool, partial(self._item_names, item_cache))

        names = _names_cache
        if argument in names:
            target = names[argument]
        else:
            with ProcessPoolExecutor() as pool:
                t = await ctx.bot.loop.run_in_executor(pool, partial(self._replace_abbr, argument))

            log.info(f'Converted query "{argument}" into "{t}" with replacements')

            if t in names:
                target = names[t]

        if not target:
            log.info(f'Item not found with query: {argument}')

        return target
