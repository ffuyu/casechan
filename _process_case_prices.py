import asyncio as aio
import json

from odmantic import field

from modules.cases import all_cases
from modules.database import Item
from modules.database import engine


async def main():
    print('Started')
    case_names = [*all_cases]
    print('Getting cases from db')
    items = await engine.find(
        Item,
        (field.in_(Item.name, case_names)),
    )
    print('Processing data')
    j = {}
    for item in items:
        case = all_cases[item.name]
        new_case = {
            'name': item.name,
            'price': item.price,
            'items': case
        }
        j[item.name] = new_case

    print('Saving data')
    with open('etc/new_cases.json', 'w') as f:
        json.dump(j, f)
    print('Finished')

    print("The following cases are missing in new_cases:")
    print(*(f'\t{c}' for c in all_cases if c not in j))


loop = aio.get_event_loop()
loop.run_until_complete(main())
