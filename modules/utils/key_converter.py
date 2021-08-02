from discord.ext.commands import Converter
from dislash import ActionRow, Button, ButtonStyle

from ..cases import Key, all_keys

__all__ = (
    'KeyConverter',
)


class KeyConverter(Converter):
    """Converts a case name string into a Case object"""

    async def convert(self, ctx, argument):
        for key in all_keys:
            lwky = key.lower()
            lwar = argument.lower()
            statements = [
                lwky == lwar,
                lwky == f'operation {lwar}',
                lwky == f'cs:go {lwar}',

                lwky.replace('case', '') == f'{lwar}',
                lwky.replace('case', '') == f'{lwar} key',
                lwky.replace('case', '') == f'operation {lwar} key',
                lwky.replace('case', '') == f'cs:go {lwar} key',
            ]
            if any(statements):
                return Key(key)
            elif lwar.replace('key', '') in lwky:
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
                message = await ctx.send(f'Did you mean **{key}**?', components=[row])

                def check(inter):
                    return inter.author == ctx.author

                try:
                    inter = await message.wait_for_button_click(check=check, timeout=15)
                except:
                    pass
                else:
                    if inter.clicked_button.custom_id == 'yes':
                        return Key(key)
                finally:
                    await message.delete()
        else:
            raise ValueError(f'No key with name "{argument}"')
