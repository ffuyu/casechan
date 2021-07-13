import asyncio

from modules.cases import open_case
from modules.database import Item


async def main(n: int):
    print('Inventory to embed')
    inv = {'R8 Revolver | Grip (Minimal Wear)': [(0.09809759804300464, 251)]}
    item_name = 'R8 Revolver | Grip (Minimal Wear)'
    item = await Item.get(name=item_name)
    variants = inv[item_name]
    print(item.to_embed(*variants[0]).to_dict())

    print('open case')
    item, *stats = await open_case('Clutch Case')
    print(item, stats)



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(1))
