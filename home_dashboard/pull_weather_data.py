# Using OpenWeather API for weather data
# https://openweathermap.org/




import requests, os, json
from datetime import datetime

import pandas as pd


# this is the API key I have for OpenWeatherMap
def _API_KEY():
    return os.environ.get('OPENWEATHERMAP_API_KEY', 'NULL')
    
def _wind_degree_to_direction(degree):
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    
    index = int((degree + 11.25) / 22.5)
    return directions[index % 16]
    

def _extract_temperature(data, status_type='current'):
    if status_type == 'current':
        data = data['current']
    temp = data['temp']
    return round(temp)
    
    
def _extract_description(data, status_type='current'):
    if status_type == 'current':
        data = data['current']
    description = data['weather'][0]['description']
    return description


def _extract_wind_speed(data, status_type='current'):
    if status_type == 'current':
        data = data['current']
    wind_speed = data['wind_speed']
    return round(wind_speed)
    
    
def _extract_wind_direction(data, status_type='current'):
    if status_type == 'current':
        data = data['current']
    wind_degree = data['wind_deg']
    wind_direction = _wind_degree_to_direction(wind_degree)
    return wind_direction
    

def _extract_pressure(data, status_type='current'):
    if status_type == 'current':
        data = data['current']
    pressure = data['pressure']
    return pressure


def _extract_sunset(data, status_type='current'):
    if status_type == 'current':
        data = data['current']
    sunset_unixtime = data['sunset']
    dt_object = datetime.fromtimestamp(sunset_unixtime)
    sunset_time = dt_object.strftime('%I:%M %p').lstrip('0')
    return sunset_time
    
def _extract_sun_dict(data, status_type='current'):
    if status_type == 'current':
        data = data['current']
    sunset_unixtime = data['sunset']
    dt_object = datetime.fromtimestamp(sunset_unixtime)
    sunset_time = dt_object.strftime('%I:%M %p').lstrip('0')
    return sunset_time


def pull_current_weather(data):
    weather_data = {
        'location': 'Alexandria, VA',
        'temperature': f'{_extract_temperature(data)}°F',
        'description': _extract_description(data),
        'wind': f'{_extract_wind_speed(data)} mph {_extract_wind_direction(data)}',
        'pressure': _extract_pressure(data),
        'sunset': _extract_sunset(data)
    }

    return weather_data
    
    
def pull_hourly_forecast(data):
    hourly_forecasts = data['hourly'][:8]  # Get the first 8 hours of forecasts

    hourly_forecast_list = list()
    for hourly_forecast in hourly_forecasts:
        time = datetime.fromtimestamp(hourly_forecast['dt']).strftime('%I:%M %p').lstrip('0')
        
        weather_data = {
            'time': time,
            'temperature': f"{_extract_temperature(hourly_forecast, status_type='hourly')}°F",
            'weather': _extract_description(hourly_forecast, status_type='hourly'),
            'wind': f"{_extract_wind_speed(hourly_forecast, status_type='hourly')} mph {_extract_wind_direction(hourly_forecast, status_type='hourly')}",
            'precip': '100%'
        }
        hourly_forecast_list.append(weather_data)
        
    return hourly_forecast_list


def pull_daily_forecast(data):
    daily_forecasts = data['daily'][1:8]  # Get the first 8 hours of forecasts

    daily_forecast_list = list()
    for daily_forecast in daily_forecasts:
        date = datetime.fromtimestamp(daily_forecast['dt']).strftime("%b %d")
        day = datetime.fromtimestamp(daily_forecast['dt']).strftime("%A")
        
        weather_data = {
            'date': date,
            'day': day,            
            'hightemp': f"{round(daily_forecast['temp']['max'])}°F",
            'lowtemp': f"{round(daily_forecast['temp']['min'])}°F",
            'weather': daily_forecast['weather'][0]['description'],
            'wind': f"{round(daily_forecast['wind_speed'])} mph {_wind_degree_to_direction(daily_forecast['wind_deg'])}"
        }
        daily_forecast_list.append(weather_data)
        
    return daily_forecast_list
    

def weather_api_call():
    api_key = _API_KEY()
    
    # Alexandria, VA
    lat = "38.8048"
    lon = "-77.0469"
    exc = 'minutely,alerts'
        
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={exc}&appid={api_key}&units=imperial"
    response = requests.get(url)
    
    if response.status_code == 401:
        print(f'Weather data status code 401 with API Key "{api_key}".')
        with open('datacache/default_weather_data.json', 'r') as f:
        
            return json.loads(f.read())
        
    return response.json()
    
    
def handle_daily_sun():
    
    sun_json_path = 'datacache/temp_daily_sun.json'
    
    def _write():
        data = weather_api_call()
        sun_json = {'current_date': datetime.today().date().strftime("%Y-%m-%d")}
        sun_json['sun_list'] = [{'date': d['dt'], 'rise': d['sunrise'], 'set': d['sunset']} for d in data['daily']]
        with open(sun_json_path, 'w') as f:
            f.write(json.dumps(sun_json))
                
    try:
        with open(sun_json_path, 'r') as f:
            sun_json = json.loads(f.read())
        if datetime.today().date().strftime("%Y-%m-%d") > sun_json['current_date']:
            _write()
    except FileNotFoundError:  # create dummy JSON with yesterday's values if file DNE
        _write()
        
    with open(sun_json_path, 'r') as f:
        sun_json = json.loads(f.read())
       
    return sun_json