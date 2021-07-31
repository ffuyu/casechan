from discord.ext.commands.errors import CommandError

__all__ = (
    'TradeError',
    'TradeNotAllowed',
    'TradeExpired',
    'TradeUnavailable'

    'ItemError'
    'ItemNotFound',
    'ItemUnavailable',
    'ItemMissingStats'

    'OpeningError'
    'MissingCase',
    'MissingKey',

    'InventoryError'
    'MissingSpace',
    'MissingItem'

    'MarketError',
    'InsufficientBalance',
    'NotMarketable'
)


class TradeError(CommandError):
    pass
class TradeNotAllowed(TradeError):
    pass
class TradeExpired(TradeError):
    pass
class TradeUnavailable(TradeError):
    pass
class NotTradeable(TradeError):
    pass



class ItemError(CommandError):
    pass
class ItemNotFound(ItemError):
    pass
class ItemUnavailable(ItemError):
    pass
class ItemMissingStats(ItemError):
    pass
class ItemMissingPrice(ItemError):
    pass


class OpeningError(CommandError):
    pass
class MissingCase(OpeningError):
    pass
class MissingKey(OpeningError):
    pass



class InventoryError(CommandError):
    pass
class MissingSpace(InventoryError):
    pass
class MissingItem(InventoryError):
    pass


class MarketError(CommandError):
    pass
class InsufficientBalance(MarketError):
    pass
class NotMarketable(MarketError):
    pass
class StateNotEqual(MarketError):
    pass

