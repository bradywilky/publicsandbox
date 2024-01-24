import requests
import json
from datetime import datetime

from bs4 import BeautifulSoup


def _get_date(event):
    return event.find('div', {'class': 'date'}).attrs['title']

def _get_time(event):
    return event.find('div', {'class': 'status'}).contents[0].replace('\t', '').replace('\n', '')

def _get_venue(event):
    if len(event.find_all('a')) > 1:
        return event.find_all('a')[-1].attrs['title']
    else:
        return event.find('a').attrs['title']

def _get_opp(event):
    if _get_venue(event) != 'Home':
        return event.find('span', {'class': 'font-weight-normal normal'}).find('span', {'class': 'team-name'}).contents[0]
    else:
        return event.find('span', {'class': 'font-weight-bold bold'}).find('span', {'class': 'team-name'}).contents[0]
    
    
url = 'https://www.emuroyals.com/sports/bsb/2022-23/schedule'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'})

soup = BeautifulSoup(r.content)

event_list = soup.find_all('div', {'class': 'event-info clearfix'})

games_html = ''

for i in event_list:
    games_html += f'{_get_date(i)} at {_get_time(i)}: {_get_opp(i)} ({_get_venue(i)})<br>'

# first reading template HTML
html_path = 'C:/Users/15714/Documents/repositories/publicsandbox/sports_schedule/schedules.html'
with open(html_path, 'r') as f:
    html_script = f.read()

# next, replacing the placeholder string with EMU future games
html_path = 'C:/Users/15714/Documents/repositories/publicsandbox/sports_schedule/schedules.html'
with open(html_path, 'w') as f:
    html_script = html_script.replace('EMU_GAMES_SWITCH', games_html)
    f.write(html_script)