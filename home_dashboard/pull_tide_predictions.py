import json, requests
from datetime import datetime, timedelta

import pandas as pd


def _yesterday():
    return datetime.now() + timedelta(days=-1)
    
    
def _today():
    return datetime.now()


def _tomorrow():
    return datetime.now() + timedelta(days=1)

def _twmorrow():
    return datetime.now() + timedelta(days=2)

    
def _get_raw_prediction_pddf(begin_date='20200101', end_date='20200101'):
    # Specify the API endpoint
    base_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

    # Specify your parameters
    params = {
        'begin_date': begin_date,  # Start date (YYYYMMDD)
        'end_date': end_date,    # End date (YYYYMMDD)
        'station': '8594900',      # Station ID
        'product': 'predictions',        # Type of data
        'datum': 'MLLW',           # Datum
        'units': 'english',        # Units (english/metric)
        'time_zone': 'lst',        # Time Zone
        'format': 'json',          # Format of the response
        'application': 'your_app_name',  # Your application name
        'interval': 'hilo'         # Interval (e.g., high/low tide)
    }

    # Make the request
    response = requests.get(base_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        
        with open('datacache/temp_tide_pred.txt', 'w') as f:
            f.write(json.dumps(response.json()))
        return pd.DataFrame(response.json()['predictions'])[['t', 'type']]
    else:
        try:
            with open('datacache/temp_tide_pred.txt', 'r') as f:
                response_json = json.loads(f.read())    
            return pd.DataFrame(response_json['predictions'])[['t', 'type']]
        except:
            return pd.DataFrame(columns=['t', 'type'])
        
def _format_prediction_pddf(pddf_raw):
    pddf = pddf_raw.rename(columns={'t': 'Timestamp', 'type': 'Tide'})
    
    val_subs = {'H': 'High', 'L': 'Low'}
    pddf['Tide'] = pddf['Tide'].replace(val_subs)
    pddf['Timestamp'] = pd.to_datetime(pddf['Timestamp'], format='%Y-%m-%d %H:%M')
    
    return pddf
    
    
def _get_prediction_pddf(begin_date, end_date):
    pddf_raw = _get_raw_prediction_pddf(begin_date, end_date)
    pddf_fmt = _format_prediction_pddf(pddf_raw)
    
    return pddf_fmt
    
   
def _get_closest_tide(proximity):
    prediction_pddf = _get_prediction_pddf(
        begin_date=_yesterday().strftime('%Y%m%d'),
        end_date=_tomorrow().strftime('%Y%m%d')
    )
    prediction_pddf['difference_to_now'] = prediction_pddf['Timestamp'] - _today()
    prediction_pddf['abs_difference_to_now'] = abs(prediction_pddf['difference_to_now'])
    
    if proximity == 'prior':
        proximity_tides = prediction_pddf[prediction_pddf['difference_to_now'] <= pd.Timedelta(0)]
    else:
        proximity_tides = prediction_pddf[prediction_pddf['difference_to_now'] > pd.Timedelta(0)]
    
    proximity_abs_difference_to_now = min(proximity_tides['abs_difference_to_now'])
    closest_prediction = proximity_tides[proximity_tides['abs_difference_to_now'] == proximity_abs_difference_to_now]
    
    return closest_prediction
 
    
def get_closest_tide_display_strings():
    
    tide_icon_fname_sub = {
        'High': 'hightide',
        'Low': 'lowtide'
    }
    
    display_strings = dict()
    display_strings['current'] = dict()
    for i in ['prior', 'next']:
        closest_prediction = _get_closest_tide(i)
        tide = closest_prediction['Tide'].iloc[0]
        formatted_time = closest_prediction['Timestamp'].dt.strftime('%I:%M %p, %b %d').str.lstrip('0').iloc[0].split(',')[0]
        
        display_strings_one_tide = dict()
        display_strings_one_tide['tide'] = tide
        display_strings_one_tide['time'] = formatted_time
        display_strings_one_tide['fname'] = tide_icon_fname_sub[tide]
        
        display_strings[i] = display_strings_one_tide
        
    if display_strings['prior']['tide'] == 'High':
        
        display_strings['current']['tide'] = 'Falling'
        display_strings['current']['fname'] = 'falling'
    else:
        display_strings['current']['tide'] = 'Rising'
        display_strings['current']['fname'] = 'rising'
    
    return display_strings
        


def get_future_tides_display_data():
    df = _get_prediction_pddf(
        begin_date=_today().strftime('%Y%m%d'),
        end_date=_twmorrow().strftime('%Y%m%d')
    )
    
    df = df[df['Timestamp'] >= _today()]
    
    # hacky way of getting next 8 tides after immediate next tide
    df = df.nsmallest(9, 'Timestamp')
    df = df.nlargest(8, 'Timestamp')
    df = df.nsmallest(8, 'Timestamp')
    
    df['formatted_time'] = df['Timestamp'].dt.strftime('%I:%M %p, %b %d').str.lstrip('0').str.split(',').str[0]
    df['day'] = df['Timestamp'].dt.strftime('%A')
    relative_day_subs = {
        _today().strftime('%A'): 'today',
        _tomorrow().strftime('%A'): 'tomorrow',
        _twmorrow().strftime('%A'): _twmorrow().strftime('%A')
    }
    df['relative_day'] = df['day'].map(relative_day_subs)

    display_list = list()
    for index, row in df.iterrows():
        if row['Tide'] == 'High':
            fname = 'hightide'
        else:
            fname = 'lowtide'
        prediction_dict = {
            'fname': fname,
            'time': row['formatted_time'],
            'relative_day': row['relative_day'],
        }
        display_list.append(prediction_dict)
    return display_list