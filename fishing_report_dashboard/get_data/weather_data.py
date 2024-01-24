from datetime import datetime

import pandas as pd
from meteostat import Point, Daily, Hourly

from utils import c_to_f


def get_historical_weather(lat, lon, start_dt = None, end_dt = None):
    
    location = Point(lat, lon)
  
    data = Hourly(location, start_dt, end_dt)
    data = data.fetch()
    
    # moving time from index to column
    data.reset_index(inplace=True)
    
    # converting time column from str to datetime
    data['datetime'] = data['time'].apply(lambda x: x.to_pydatetime())
    data = data.drop('time', axis=1)
    
    # converting temperature to Fahrenheit
    if 'temp' in data.columns:
        data['temp'] = data['temp'].apply(lambda x: c_to_f(x))
        
    # mapping weather name codes to "coco" column
    meteo_meta_url = 'https://dev.meteostat.net/formats.html#meteorological-parameters'
    
    # using 'Heavy Freezing Rain' as hacky way to match table
    coco_meaning = pd.read_html(meteo_meta_url, match = 'Heavy Freezing Rain')[0]
    coco_meaning = coco_meaning.rename({'Code': 'coco'}, axis='columns')
    
    data = pd.merge(data, coco_meaning, on='coco').drop('coco', axis = 1)
    
    data = data.rename(columns={'temp': 'air_temp'})
    
    return data