import requests
import json
from datetime import datetime

from bs4 import BeautifulSoup


url = 'https://hokiesports.com/sports/mens-basketball/schedule/2022-23'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'})

soup = BeautifulSoup(r.content, features='lxml')

games_html = [y for y in soup.find_all('script') if 'type' in y.attrs.keys() and y.attrs['type'] == 'application/ld+json'][0]

games_json = json.loads(str(games_html.contents[0]))

today = datetime.today()

future_games = list()

for g in games_json:
    if datetime.strptime(g['startDate'], '%Y-%m-%dT%H:%M:%S') >= today:
      
        future_games.append((g['startDate'], g['description']))
        

future_games = sorted(future_games, key = lambda x: x[0])

line = '|' + ('-' * 60)
for g in future_games:
    print(f'{line}\n| {g[1].replace("Virginia Tech", "VT")}')
    if g == future_games[-1]:
        print(line)