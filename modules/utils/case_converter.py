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
                    any([x.isdigit() for x in argument]) and any([x.isdigit() for x in lwcs]) and (argument in lwcs or argument.replace('case', '') in lwcs),
                    # argument has digits
                    # case name has digits
                    # argument is in case name
                    not any([x.isdigit() for x in argument]) and not any([x.isdigit() for x in lwcs]) and (argument in lwcs or argument.replace('case', '') in lwcs),
                    # argument has no digits
                    # case name has no digits
                    # argument is in case name
                    
                    ('xray' in argument or 'x-ray' in argument) and argument.replace('xray', 'x-ray') in lwcs # specifically for x-ray p250 package
                ]
                if any(statements_secondary):
                    return Case(case)
        else:
            raise ValueError(f'No case with name "{argument}"')
