import asyncio

from modules.database import Player

m = Player(member_id=123, guild_id=456)


async def main():
    await asyncio.gather(
        *[m.open_case('Clutch Case') for _ in range(1000)]
    )
    print('Finished iteration')


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
