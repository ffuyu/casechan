from discord.ext.commands import Converter
from dislash import ActionRow, Button, ButtonStyle

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
            ]
            if any(statements):
                return Key(key)
            elif lwar.replace('key', '') in lwky:
                if ctx.author.id in list(player_preferences.keys()):
                    if player_preferences.get(ctx.author.id, {}).get(lwar.replace('key', ''), None):

                        return Key(key)
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
                        if player_preferences.get(ctx.author.id, 0):
                            player_preferences[ctx.author.id][lwar.replace('key', '')] = key
                        else:
                            player_preferences[ctx.author.id] = {
                                lwar.replace('key', ''): key
                            }
                        return Key(key)
                finally:
                    await message.delete()
        else:
            raise ValueError(f'No key with name "{argument}"')
