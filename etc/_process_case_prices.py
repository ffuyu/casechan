import asyncio as aio
import json

from odmantic import field

from modules.containers import all_cases, case_assets
from modules.database import Item
from modules.database import engine

_require_no_key = {
    "X-Ray P250 Package"
}

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
            'items': case,
            'key': f'{item.name} Key' if item.name not in _require_no_key else None
        }
        j[item.name] = new_case

    print('Adding assets to cases')

    for case in j:
        asset = case_assets.get(case)
        j[case]['asset'] = asset

    print('Saving data')
    with open('etc/new_cases.json', 'w') as f:
        json.dump(j, f)
    print('Finished')

    print("The following cases are missing in new_cases:")
    print(*(f'\t{c}\n' for c in all_cases if c not in j))


loop = aio.get_event_loop()
loop.run_until_complete(main())
