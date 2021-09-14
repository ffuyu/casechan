from modules.utils.misc import first
from modules.constants import ButtonTypes
from discord.ext.commands import Converter
from dislash.interactions.message_components import ActionRow, Button

from ..cases import Case, Package, all_cases, all_packages, all_capsules

__all__ = (
    'ContainerConverter',
)

player_preferences = {}


class ContainerConverter(Converter):
    """
    Converts a case name into a Case, Package or a Sticker Capsule
    Also converts key names to case key names
    """

    async def convert(self, ctx, argument:str):
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
                lwcs == f'{argument} souvenir package',

                lwcs == f'katowice 2019 {argument} package',
                lwcs == f'katowice 2019{argument} souvenir package',

                lwcs == f'berlin 2019 {argument} package',
                lwcs == f'berlin 2019{argument} souvenir package',
                
                lwcs == f'london 2018 {argument} package',
                lwcs == f'london 2018 {argument} souvenir package',

                lwcs == f'boston 2018 {argument} package',
                lwcs == f'boston 2018{argument} souvenir package',

                lwcs == f'krakow 2017 {argument} package',
                lwcs == f'krakow 2017 {argument} souvenir package',

                lwcs == f'atlanta 2017 {argument} package',
                lwcs == f'atlanta 2017 {argument} souvenir package',

                lwcs == f'cologne 2016 {argument} package',
                lwcs == f'cologne 2016 {argument} souvenir package',

                lwcs == f'mlg columbus 2016 {argument} package',
                lwcs == f'mlg columbus 2016 {argument} souvenir package',

                lwcs == f'dreamhack cluj-napoca 2015 {argument} package',
                lwcs == f'dreamhack cluj-napoca 2015  {argument} souvenir package',

                lwcs == f'esl one cologne 2015 {argument} package',
                lwcs == f'esl one cologne 2015 {argument} souvenir package',

                lwcs == f'esl one katowice 2015 {argument} package',
                lwcs == f'esl one katowice 2015 {argument} souvenir package',

                lwcs == f'dreamhack 2014 {argument} package',
                lwcs == f'dreamhack 2014 {argument} souvenir package',

                lwcs == f'esl one cologne 2014 {argument} package',
                lwcs == f'esl one cologne 2014 {argument} souvenir package',

                lwcs == f'ems one 2014 {argument} package',
                lwcs == f'ems one 2014 {argument} souvenir package',

                lwcs == f'dreamhack 2013 {argument} package',
                lwcs == f'dreamhack 2013 {argument} souvenir package'
            ]
            # secondary = [
            #     any([x.isdigit() for x in argument]) and any([x.isdigit() for x in lwcs]) and (argument in lwcs or argument.replace('package', '') in lwcs),
            #     not any([x.isdigit() for x in argument]) and not any([x.isdigit() for x in lwcs]) and (argument in lwcs or argument.replace('package', '') in lwcs),
            # ]

            if any(primary): 
                return Package(package)
            # elif any(secondary):
            #     return Package(package)


        raise ValueError(f'No container or key with name "{argument}"')
