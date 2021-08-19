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
                lwky.replace('case', '') == f'operation {lwar} weapon case key',
            ]
            if any(statements):
                return Key(key)
            elif lwar.replace('key', '') in lwky:
                lwar_ = lwar.replace('KEY', '')
                if ctx.author.id in player_preferences:
                    if player_preferences[ctx.author.id].get(lwar_, None):

                        return Key(key)
                row = ActionRow(
                    Button(
                        style=ButtonTypes.CONFIRM,
                        label='Yes',
                        custom_id='yes'
                    ),
                    Button(
                        style=ButtonTypes.CANCEL,
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
                        p = player_preferences.setdefault(ctx.author.id, {})
                        p[lwar_] = key
                        return Key(key)
                finally:
                    await message.delete()
        else:
            raise ValueError(f'No key with name "{argument}"')
