from discord.ext.commands import Converter
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle

from ..cases import Case, all_cases

__all__ = (
    'CaseConverter',
)

player_preferences = {}


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
                lwcs == f'operation {lwar} case',
                lwcs == f'cs:go {lwar}',
                lwcs == f'cs:go {lwar} case',
                lwcs == f'operation {lwar} weapon case',
            ]
            if any(statements):
                return Case(case)
            elif lwar.replace('case', '') in lwcs or lwar.replace('xray', 'x-ray') in lwcs:
                lwar_ = lwar.replace('case', '')
                if ctx.author.id in player_preferences:
                    if player_preferences[ctx.author.id].get(lwar_, None):
                        return Case(case)

                row = ActionRow(
                    Button(
                        style=ButtonStyle.green,
                        label='Yes',
                        custom_id='yes'
                    ),
                    Button(
                        style=ButtonStyle.red,
                        label='No',
                        custom_id='no'
                    )
                )
                message = await ctx.send(f'Did you mean **{case}**?', components=[row])

                def check(inter):
                    return inter.author == ctx.author

                try:
                    inter = await message.wait_for_button_click(check=check, timeout=15)
                except:
                    pass
                else:
                    if inter.clicked_button.custom_id == 'yes':
                        p = player_preferences.setdefault(ctx.author.id, {})
                        p[lwar_] = case
                        return Case(case)
                finally:
                    await message.delete()
        else:
            raise ValueError(f'No case with name "{argument}"')
