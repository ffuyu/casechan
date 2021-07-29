from discord.ext.commands import Converter

from ..cases import Case, all_cases

__all__ = (
    'CaseConverter',
)


class CaseConverter(Converter):
    """Converts a case name string into a Case object"""

    async def convert(self, ctx, argument):
        if argument in all_cases:
            return Case(argument)
        else:
            raise ValueError(f'No case with name "{argument}"')
