import pandas as pd
from src.constants import FLAGS_URL

def isNaN(num):
    return num != num

df = pd.read_csv(FLAGS_URL)
temp = dict[str, dict[str, int|str]]()
for item in df.to_dict(orient='records'):
    if isNaN(item['id']) or isNaN(item['flag']) or isNaN(item['name']) or isNaN(item['amount']):
        continue
    item.pop("備註")
    temp[item['flag']] = item

with open('data/flags.json', 'w', encoding='utf-8') as f:
    f.write('{\n')
    for idx, (key, value) in enumerate(temp.items()):
        if idx != 0:
            f.write(',\n')
        content = str(value).replace("'", '"')
        f.write(f'"{key}": {content}')
    f.write('\n}\n')