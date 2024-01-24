import requests
import json
from datetime import datetime

from bs4 import BeautifulSoup


url = 'https://hokiesports.com/sports/mens-basketball/schedule/2022-23'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'})

soup = BeautifulSoup(r.content)

games_html = [y for y in soup.find_all('script') if 'type' in y.attrs.keys() and y.attrs['type'] == 'application/ld+json'][0]

games_json = json.loads(str(games_html.contents[0]))

today = datetime.today()

# extracting game date and description and storing them in a list
future_games = list()

for g in games_json:
    if datetime.strptime(g['startDate'], '%Y-%m-%dT%H:%M:%S') >= today:
        future_games.append((g['startDate'], g['description']))

# reordering list by date
future_games = sorted(future_games, key = lambda x: x[0])

# creating string with each game description followed by HTML tag to create new line
games_html = ''

for g in future_games:
    games_html += f'{g[1]}<br>'

# first reading template HTML
html_path = 'C:/Users/15714/Documents/repositories/publicsandbox/sports_schedule/schedules_template.html'
with open(html_path, 'r') as f:
    html_script = f.read()

# next, replacing the placeholder string with VT future games
html_path = 'C:/Users/15714/Documents/repositories/publicsandbox/sports_schedule/schedules.html'
with open(html_path, 'w') as f:
    html_script = html_script.replace('VT_GAMES_SWITCH', games_html)
    f.write(html_script)