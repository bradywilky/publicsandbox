from dateutil import rrule
import datetime

import pandas as pd
from suntime import Sun, SunTimeException


def _timedelta_to_hours(td):
    seconds = td.total_seconds()
    minutes = seconds / 60 
    hours = minutes / 60
    
    return hours


def get_sun_data(latitude, longitude, start, end):
    
    df = pd.DataFrame(columns = ['sundata_lat', 'sundata_lon', 'date', 'sunrise', 'sunset', 'sun_hours'])
    sun = Sun(latitude, longitude)

    for dt in rrule.rrule(rrule.DAILY, dtstart = start, until = end):
        abd = dt.date()
        abd_sr = sun.get_local_sunrise_time(abd)
        abd_ss = sun.get_local_sunset_time(abd)
        
        row = {
            'sundata_lat' : latitude,
               'sundata_lon' : longitude,
               'date' : abd,
               'sunrise' : abd_sr.replace(tzinfo=None),
               'sunset' : abd_ss.replace(tzinfo=None),
               'sun_hours' : _timedelta_to_hours(abd_ss - abd_sr)
        }
        
        df = df.append(row, ignore_index = True)
        
    return df