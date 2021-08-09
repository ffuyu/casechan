from discord.ext.commands import Converter

__all__ = (
    'OperatorConverter',
)

operators = {
    "gt": ">",
    "lt": "<",
    "eq": "="
}

class OperatorConverter(Converter):
    """Does not convert, checks if string operator is valid and raises ValueError otherise."""

    async def convert(self, ctx, argument):
        if argument in [">", "<", "="]:
            return argument
        elif argument in [*operators]:
            return operators.get(argument)
        else:
            raise ValueError(f'No operator with name "{argument}"')
