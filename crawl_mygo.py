import requests

url = 'https://mygoapi.miyago9267.com/mygo/all_img'

respond = requests.get(url).json()['urls']
for res in respond:
    print(res['alt'])
