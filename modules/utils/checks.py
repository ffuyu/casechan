from modules.config import OWNERS_IDS
from modules.errors import MarketError, NotAllowed, UnableToBuy, UnableToOpen, UnableToSell
from modules.containers import Capsule, Case, Container, Key, Package

from modules.database import Player, Item

import re

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
    elif not remaining_inv >= amount and not isinstance(item, (Container, Key)):
        raise UnableToBuy(
            message='You can\'t complete this purchase, your inventory is full!'
        )
    elif not item.price:
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
    elif not isinstance(item, (Container, Item)):
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

        elif isinstance(item, Capsule):
            if not player.capsules.get(item.name, 0) >= amount:
                raise UnableToSell(
                    message=f'You are missing {missing_items}x {item.name}.'
                )

        elif isinstance(item, Package):
            if not player.packages.get(item.name, 0) >= amount:
                raise UnableToSell(
                    message=f'You are missing {missing_items}x {item.name}.'
                )

    return True

def able_to_opencontainer(player:Player, container:Union[Case, Package, Capsule], amount:int=1):
    if isinstance(container, Case):
        container_amount = player.cases.get(container.name, 0)
    elif isinstance(container, Package):
        container_amount = player.packages.get(container.name, 0)
    # elif isinstance(container, Capsule):
    #     if player.member_id not in OWNERS_IDS:
    #         raise NotAllowed('You are not allowed to open this container')

        container_amount = player.capsules.get(container.name, 0)
    
    # if container requires a key
    if container.key: key_amount = player.keys.get(container.key.name, 0) 
    else: key_amount = None

    inv_lim_amount = player.inventory_limit - player.inv_items_count
    
    if container_amount < amount: raise UnableToOpen(message=f'You are missing {amount - container_amount}x {container.name}')

    elif key_amount is not None and key_amount < amount: raise UnableToOpen(message=f'You are missing {amount - key_amount}x {container.key.name}')

    elif inv_lim_amount < amount:raise UnableToOpen(message=f'You can\'t open more cases, your inventory is full!')

    elif amount > 1000: raise UnableToOpen('You cannot open more than 1000 cases at once!')

    return True

def emojify(ctx, text:str) -> str:
    """
    Clears custom emojis from the text if guild does not allow external emotes for the bot
    """
    if not ctx.guild.me.guild_permissions.external_emojis: return re.sub(r'<.+?>', '', text)

    return text
