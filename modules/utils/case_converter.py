from modules.constants import ButtonTypes
from discord.ext.commands import Converter
from dislash.interactions.message_components import ActionRow, Button

from ..cases import Case, all_cases

__all__ = (
    'CaseConverter',
)

player_preferences = {}


class CaseConverter(Converter):
    """Converts a case name string into a Case object"""

    async def convert(self, ctx, argument:str.lower):
        for case in [*all_cases]:
            lwcs = case.lower()
            statements_primary = [
                lwcs == argument,
                lwcs == f'{argument} case',
                lwcs == f'operation {argument}',
                lwcs == f'operation {argument} case',
                lwcs == f'cs:go {argument}',
                lwcs == f'cs:go {argument} case',
                lwcs == f'operation {argument} weapon case',
            ]
            if any(statements_primary):
                return Case(case)
            else:
                statements_secondary = [
                    argument in lwcs,
                    argument.replace('case', '') in lwcs,
                    argument.replace('xray', 'x-ray') in lwcs
                ]
                if any(statements_secondary):
                    return Case(case)
        else:
            raise ValueError(f'No case with name "{argument}"')
