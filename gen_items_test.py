import asyncio as aio
import time
from modules.database import Item
from modules.cases import all_cases, Case


async def foo():
    exts = set()
    for case in all_cases:
        c = Case(case)
        items = await c.get_items()
        exteriors = {it.exterior for it in items if it.exterior}
        exts.update(exteriors)
    print(exts)


async def bar():
    for case in all_cases:
        c = Case(case)
        [await c.open() for _ in range(100)]


async def pip():
    css = [*all_cases]
    t1 = time.perf_counter()
    c = Case(css[10])
    await c.open()
    t2 = time.perf_counter()
    print(f'total time: {t2 - t1}')

    t1 = time.perf_counter()
    c = Case(css[10])
    await c.open()
    t2 = time.perf_counter()
    print(f'total time: {t2 - t1}')


l = aio.get_event_loop()
l.run_until_complete(pip())
