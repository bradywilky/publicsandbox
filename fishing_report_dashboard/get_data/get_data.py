from weather_data import get_historical_weather
from water_data import get_usgs_water_data


get_usgs_water_data(site, param_cd, start_dt, end_dt)

get_historical_weather(lat, lon, start = None, end = None)