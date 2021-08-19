from modules.errors import UnableToBuy, UnableToOpen, UnableToSell
from modules.cases import Case, Key

from modules.database import Player, Item

from typing import Union

def able_to_buy(player:Player, item:Union[Item, Case, Key], amount:int=1):
    total_price = item.price * amount
    remaining_inv = player.inventory_limit - player.inv_items_count
    
    if player.trade_banned:
        raise UnableToBuy(
            message='Your buying functions are disabled.'
        )
    elif not amount <= 1000:
        raise UnableToBuy(
            message='You can\'t buy more than 1000 items at once.'
        )
    elif not remaining_inv >= amount and not isinstance(item, (Case, Key)):
        raise UnableToBuy(
            message='You can\'t complete this purchase, your inventory is full!'
        )
    elif not item.price and isinstance(item, (Item, Key)):
        raise UnableToBuy(
            message='You can\'t purchase this item as it has no price data.'
        )
    elif not player.balance >= total_price:
        raise UnableToBuy(
            message=f'You are missing ${total_price - player.balance:.2f} to buy this item.'
        )
    
    return True

def able_to_sell(player:Player, item:Union[Item, Case, Key], amount:int=1):   
    missing_items = amount - player.item_count(item.name)
    
    if player.trade_banned:
        raise UnableToSell(
            message='Your selling functions are disabled.'
        )
    elif isinstance(item, Item) and not item.is_marketable:
        raise UnableToSell(
            message='This item cannot be sold as it has no price.'
        )
    elif not isinstance(item, (Case, Item)):
        raise UnableToSell(
            message=f'The item you are trying to sell cannot be sold in the market.'
        )

    else:

        if isinstance(item, Item):
            if not player.item_count(item.name) >= amount:
                raise UnableToSell(
                    message=f'You are missing {missing_items}x {item.name}.'
                )

        elif isinstance(item, Case):
            if not player.cases.get(item.name, 0) >= amount:
                raise UnableToSell(
                    message=f'You are missing {missing_items}x {item.name}.'
                )

    return True

def able_to_opencase(player:Player, case:Case, amount:int=1):
    case_amount = player.cases.get(case.name, 0)
    if case.key:
        key_amount = player.keys.get(case.key.name, 0)
    else:
        key_amount = None
    inv_lim_amount = player.inventory_limit - player.inv_items_count
    
    if case_amount < amount:
        raise UnableToOpen(
            message=f'You are missing {amount - case_amount}x {case}')
    elif key_amount is not None and key_amount < amount:
        raise UnableToOpen(
            message=f'You are missing {amount - key_amount}x {case.key}')
    elif inv_lim_amount < amount:
        raise UnableToOpen(
            message=f'You can\'t open more cases, your inventory is full!')

    return True