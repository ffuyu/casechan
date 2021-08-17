from modules.errors import UnableToBuy, UnableToOpen, UnableToSell
from modules.cases import Case, Key

from modules.database import Player, Item

from typing import Union

def able_to_buy(player:Player, item:Union[Item, Case, Key], amount:int=1):
    total_price = item.price * amount
    remaining_inv = player.inventory_limit - player.inv_items_count
    
    if player.trade_banned:
        raise UnableToBuy(
            content='Your buying functions are disabled.'
        )
    elif not amount <= 1000:
        raise UnableToBuy(
            message='You can\'t buy more than 1000 items at once.'
        )
    elif not remaining_inv >= amount or isinstance(item, (Case, Key)):
        raise UnableToBuy(
            message='You can\'t complete this purchase, your inventory is full!'
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
    elif not player.item_count(item.name) >= amount:
        raise UnableToSell(
            message=f'You are missing {missing_items}x {item.name}.'
        )
    elif not isinstance(item, (Case, Item)):
        raise UnableToSell(
            message=f'The item you are trying to sell cannot be sold in the market.'
        )

    return True

def able_to_opencase(player:Player, case:Case, amount:int=1):
    case_amount = player.cases.get(case.name, 0)
    key_amount = player.keys.get(case.key, 0)
    inv_lim_amount = player.inventory_limit - player.inv_items_count
    
    if case_amount < amount:
        raise UnableToOpen(
            message=f'You are missing {case_amount - amount} x {case}')
    elif key_amount < amount:
        raise UnableToOpen(
            message=f'You are missing {key_amount - amount}x {case.key}')
    elif inv_lim_amount < amount:
        raise UnableToOpen(
            message=f'You can\'t open more cases, your inventory is full!')

    return True