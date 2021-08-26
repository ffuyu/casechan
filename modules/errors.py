from discord.ext.commands.errors import CommandError


class FailedItemGen(Exception):
    pass


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


class UnableToOpen(CaseError):
    pass


class MissingCase(CommandError):
    pass


class MissingKey(CommandError):
    pass


class InventoryError(CommandError):
    pass


class MissingSpace(InventoryError):
    pass


class MissingItem(InventoryError):
    pass


class MarketError(CommandError):
    pass


class UnableToBuy(MarketError):
    pass


class UnableToSell(MarketError):
    pass


class RewardsError(CommandError):
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


class InsufficientBalance(BetError):
    pass
