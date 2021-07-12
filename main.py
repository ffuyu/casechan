import asyncio
import random
import time

from modules.cases import Case, all_cases
from modules.utils import Timer


async def main(n: int):
    c = Case()
    a = time.monotonic()

    for i in range(n):
        async with Timer():
            await c.open_case(random.choice([*all_cases]))
        if i and i % 1000 == 0:
            print(i)
    b = time.monotonic()
    print('Finished iteration', f'{b - a:.2f} seconds {n / (b - a):.2f} cases/s')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(10_000))
