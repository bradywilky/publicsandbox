import os, json, requests, inspect

from datetime import datetime, timedelta
import pandas as pd



TIDE_PRED_PATH = 'datacache/temp_tide_predictions.json'

def _write_raw_prediction_pddf(begin_date, end_date):

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
        data_json = {
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': json.dumps(response.json())
        }
        with open(TIDE_PRED_PATH, 'w') as f:
            f.write(json.dumps(data_json))
        
    else:
        print(f'Unable to get data from NOAA API ({response.status_code}).')
        try:
            with open(TIDE_PRED_PATH, 'r') as f:
                response_json = json.loads(f.read())    
                print(f'Defaulting to data from {response_json["datetime"]}.')
            return pd.DataFrame(response_json['predictions'])[['t', 'type']]
        except:
            print(f'Unable to read from {TIDE_PRED_PATH}. Using empty dataframe instead.')
            return pd.DataFrame(columns=['t', 'type'])
        

def _get_raw_prediction_pddf(begin_date, end_date):
    
    def _load_data():
        with open(TIDE_PRED_PATH, 'r') as f:
            data_json = json.loads(f.read())
        return data_json

    if os.path.exists(TIDE_PRED_PATH):
        data_json = _load_data()
        
        write_datetime = datetime.strptime(data_json['datetime'], '%Y-%m-%d %H:%M:%S')
        difference_to_call = abs(write_datetime - datetime.now())
        minute_difference_to_call = difference_to_call.total_seconds() / 60
        
        if minute_difference_to_call < 10:
            return pd.DataFrame(json.loads(data_json['data'])['predictions'])[['t', 'type']]

    _write_raw_prediction_pddf(begin_date, end_date)
    return pd.DataFrame(json.loads(_load_data()['data'])['predictions'])[['t', 'type']]
            

def _format_prediction_pddf(pddf_raw):
    pddf = pddf_raw.rename(columns={'t': 'Timestamp', 'type': 'Tide'})
    
    val_subs = {'H': 'High', 'L': 'Low'}
    pddf['Tide'] = pddf['Tide'].replace(val_subs)
    pddf['Timestamp'] = pd.to_datetime(pddf['Timestamp'], format='%Y-%m-%d %H:%M')
    
    return pddf
    
    
def get_base_tide_data(
        begin_date=(datetime.now() + timedelta(days=-1)).strftime('%Y%m%d'),
        end_date=(datetime.now() + timedelta(days=2)).strftime('%Y%m%d')
    ):
    pddf_raw = _get_raw_prediction_pddf(begin_date, end_date)
    pddf_fmt = _format_prediction_pddf(pddf_raw)
    
    return pddf_fmt