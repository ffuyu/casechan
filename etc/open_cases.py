import asyncio

from odmantic import query

from modules.database import Player, Item, engine

m = Player(member_id=123, guild_id=456)


async def main():
    # items = await engine.find(Item)
    # print(len([i for i in items if '★' in i.name]))
    #
    # print(len(items))
    for i in range(1000):
        print(i)
        print(await m.open_case('Clutch Case'))
    print('Finished iteration')


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
