"""
General miscellaneous tools
"""
from collections.abc import Sequence
from typing import Any, Optional

__all__ = (
    'first',
)


def first(seq: Sequence, **conditions) -> Optional[Any]:
    """
    Returns the first item from a sequence that has all specified conditionas
    Args:
        seq: a sequence for the lookup
        conditions: dict
            keys: object's attributes
            values: object's value for the given attribute
    """
    return next(
        (item for item in seq
         if all(getattr(item, k) == v
                for k, v in conditions.items())),
        None
    )
