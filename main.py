import asyncio
import time

from modules.cases import Case


async def main():
    c = Case()
    a = time.monotonic()
    for i in range(10_000):
        await c.open_case('Clutch Case')
        if i % 1000 == 0:
            print(i)
    b = time.monotonic()
    print('Finished iteration', f'{b - a:.2f} seconds {10_000 / (b - a):.2f} cases/s')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
