import asyncio

from modules.cases import open_case
from modules.database import Item, Player


async def main(n: int):
    print('open case')
    item, *stats = await open_case('Clutch Case')
    print(item, stats)

    p = Player(member_id=123, guild_id=456)
    p.add_item(item.name, stats)

    embed = item.to_embed(*stats)
    print(embed.to_dict())

    print(p.dict())




if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(1))
