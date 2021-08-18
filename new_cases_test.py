import asyncio as aio

from modules.database import Player
from modules.new_cases import Case


async def main():
    player = Player(guild_id=123, member_id=456)
    case = Case('CS20 Case')
    player.mod_case(case.name)
    player.mod_key(case.key.name, 1)
    print(player.cases, player.keys)
    r = await player.open_case(case.name)
    print(player.cases, player.keys)
    print(player.inventory)
    print(r)


loop = aio.get_event_loop()
loop.run_until_complete(main())