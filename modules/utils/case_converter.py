from os import stat
from discord.ext.commands import Converter

from ..cases import Case, all_cases

__all__ = (
    'CaseConverter',
)


class CaseConverter(Converter):
    """Converts a case name string into a Case object"""

    async def convert(self, ctx, argument):
        for case in all_cases:
            lwcs = case.lower()
            lwar = argument.lower()
            statements = [
                lwcs == lwar,
                lwcs == f'{lwar} case',
                lwcs == f'operation {lwar}',
                lwcs == f'operation {lwar} case'
            ]
            if any(statements):
                return Case(case)
        else:
            raise ValueError(f'No case with name "{argument}"')
