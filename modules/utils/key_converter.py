from discord.ext.commands import Converter

from ..cases import Key, all_keys

__all__ = (
    'KeyConverter',
)


class KeyConverter(Converter):
    """Converts a case name string into a Case object"""

    async def convert(self, ctx, argument):
        for key in all_keys:
            if key.lower() == argument.lower() or key.lower() == '%s key' % argument.lower():
                return Key(key)
        else:
            raise ValueError(f'No key with name "{argument}"')