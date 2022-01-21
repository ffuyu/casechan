from discord.ext.commands import Converter
import operator

__all__ = (
    'OperatorConverter',
)

operators = {
    ">": operator.gt,
    "<": operator.lt,
    "gt": operator.gt,
    "lt": operator.lt,
}

class OperatorConverter(Converter):
    """Converts a string logical operator to an actual operator object"""
    async def convert(self, ctx, argument) -> operator:
        if argument in [*operators]:
            return operators[argument]
        if any(x.isdigit() for x in argument):
            return operator.eq
        else:
            raise ValueError(f'No operator with name "{argument}"')