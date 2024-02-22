import json, requests

import pandas as pd

    
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
    
    
def get_base_tide_data(begin_date, end_date):
    pddf_raw = _get_raw_prediction_pddf(begin_date, end_date)
    pddf_fmt = _format_prediction_pddf(pddf_raw)
    
    return pddf_fmt