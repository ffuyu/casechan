from typing import Union
from modules.utils.misc import first
from modules.constants import ButtonTypes
from discord.ext.commands import Converter
from dislash.interactions.message_components import ActionRow, Button

from ..cases import Capsule, Case, Key, Package, all_cases, all_packages, all_capsules

__all__ = (
    'ContainerConverter',
)

player_preferences = {}


class ContainerConverter(Converter):
    """
    Converts a case name into a Case, Package or a Sticker Capsule
    Also converts key names to case key names
    """

    async def convert(self, ctx, argument:str) -> Union[Case, Package, Capsule, Key]:
        first_argument = argument.lower()
        argument = argument.lower().replace(' key', '')

        if len(argument) < 4:
            raise ValueError(f'No container or key with name "{argument}"')

        # cases
        for case in [*all_cases]:
            lwcs = case.lower()

            primary = [
                lwcs == argument,
                lwcs == f'{argument} case',
                lwcs == f'operation {argument}',
                lwcs == f'operation {argument} case',
                lwcs == f'cs:go {argument}',
                lwcs == f'cs:go {argument} case',
                lwcs == f'operation {argument} weapon case',
            ]

            if any(primary):
                return Case(case) if not 'key' in first_argument else Case(case).key
        
            if any([
                any([x.isdigit() for x in argument]) and any([x.isdigit() for x in lwcs]) and (argument in lwcs or argument.replace('case', '') in lwcs),
                not any([x.isdigit() for x in argument]) and not any([x.isdigit() for x in lwcs]) and (argument in lwcs or argument.replace('case', '') in lwcs),
            ]):
                return Case(case) if not 'key' in first_argument else Case(case).key

                
        # packages
        for package in [*all_packages]:
            lwcs = package.lower()
            primary = [
                lwcs == argument,
                lwcs == f'{argument} package',
                lwcs == f'{argument} souvenir package'
            ]
            secondary = [
                any([x.isdigit() for x in argument]) and any([x.isdigit() for x in lwcs]) and (argument in lwcs or argument.replace('package', '') in lwcs),
                not any([x.isdigit() for x in argument]) and not any([x.isdigit() for x in lwcs]) and (argument in lwcs or argument.replace('package', '') in lwcs),
            ]

            if any(primary): 
                return Package(package)
            elif any(secondary):
                return Package(package)

        # capsules
        for capsule in [*all_capsules]:
            print(capsule, argument, sep=' > ')
            if capsule.lower() == argument:
                return Capsule(capsule) if not 'key' in first_argument else Capsule(case).key

        raise ValueError(f'No container, package, capsule or key with name "{argument}"')
