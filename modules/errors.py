from discord.ext.commands.errors import CommandError

__all__ = (
    'TradeError',
    'TradeNotAllowed',
    'TradeExpired',

    'ItemNotFound',
    'ItemUnavailable',

    'MissingCase',
    'MissingKey',

    'MissingSpace',

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


class CaseError(CommandError):
    pass


class MissingCase(CaseError):
    pass


class MissingKey(CaseError):
    pass


class CaseNotFound(CaseError):
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


class ExceededBuyLimit(MarketError):
    pass


class SaleNotConfirmed(MarketError):
    pass


class DailyError(CommandError):
    pass


class HourlyError(DailyError):
    pass


class WeeklyError(DailyError):
    pass


class PromoError(CommandError):
    pass


class CodeExpired(PromoError):
    pass
class CodeInvalid(PromoError):
    pass
class CodeClaimed(PromoError):
    pass
class ReachedMaxUses(PromoError):
    pass


class AlreadyClaimed(PromoError):
    pass
class ExistingCode(PromoError):
    pass



class BetError(CommandError):
    pass
class InvalidBet(BetError):
    pass
class BetTooLow(BetError):
    pass
