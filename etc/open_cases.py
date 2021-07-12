import asyncio

from modules.database import Player

m = Player(member_id=123, guild_id=456)


async def main():
    for i in range(1000):
        print(await m.open_case('Clutch Case'))
    print('Finished iteration')


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
