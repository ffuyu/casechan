from modules.constants import ButtonTypes
from discord.ext.commands import Converter
from dislash import ActionRow, Button

from ..cases import Key, all_keys

__all__ = (
    'KeyConverter',
)

player_preferences = {}

class KeyConverter(Converter):
    """Converts a key name string into a Key object"""
    async def convert(self, ctx, argument:str.lower):
        for key in all_keys:
            lwky = key.lower()
            statements = [
                lwky == argument,
                lwky == f'operation {argument}',
                lwky == f'cs:go {argument}',

                lwky.replace('case', '') == f'{argument}',
                lwky.replace('case', '') == f'{argument} key',
                lwky.replace('case', '') == f'operation {argument} key',
                lwky.replace('case', '') == f'cs:go {argument} key',
                lwky.replace('case', '') == f'operation {argument} weapon case key',
                

                len(lwky.split()) > 2 and lwky == f'{argument.split()[0]} {argument.split()[1]} case {argument.split()[-1]}',
                # This splits the argument word by word and places the word 'case' in between both first and the last argument
                # This only triggers when the argument's word count is greater than 2 (and mainly 3) because this is intented to work with
                # Numbered cases, such as Spectrum 2, Chroma 2, Chroma 3...

                len(lwky.split()) > 1 and lwky == f'{argument.split()[0]} case {argument.split()[-1]}'
                # This check is similar to the check above and the only difference is that it works with word count greater than 2
                # This check does not put the second word into the final string for compatiblity with non-numbered cases such as:
                # Clutch Case, Spectrum Case, Prisma Case...

                # We do not check if word count is 1 to prevent conflicts with CaseConverter.
                

            ]
            if any(statements):
                return Key(key)

        raise ValueError(f'No case with name "{argument}"')
