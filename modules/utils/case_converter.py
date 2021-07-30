from discord.ext.commands import Converter

from ..cases import Case, all_cases

__all__ = (
    'CaseConverter',
)


class CaseConverter(Converter):
    """Converts a case name string into a Case object"""

    async def convert(self, ctx, argument):
        for case in all_cases:
            if case.lower() == argument.lower() or case.lower() == '%s case' % argument.lower():
                return Case(case)
        else:
            raise ValueError(f'No case with name "{argument}"')
