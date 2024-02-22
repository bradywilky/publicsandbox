from datetime import datetime, timedelta

import pandas as pd

from pull_base_tide_data import get_base_tide_data


def _yesterday():
    return datetime.now() + timedelta(days=-1)
    
    
def _today():
    return datetime.now()


def _tomorrow():
    return datetime.now() + timedelta(days=1)


def _twmorrow():
    return datetime.now() + timedelta(days=2)
    

BASE_TIDE_DATA = get_base_tide_data(
    _yesterday().strftime('%Y%m%d'),
    _twmorrow().strftime('%Y%m%d')
)


def _filter_tide_data(begin_date, end_date):
    begin_filter = (BASE_TIDE_DATA['Timestamp'].dt.strftime('%Y%m%d') >= begin_date)
    end_filter = (BASE_TIDE_DATA['Timestamp'].dt.strftime('%Y%m%d') <= end_date)
    return BASE_TIDE_DATA[begin_filter & end_filter]


def _get_closest_tide(proximity):
    prediction_pddf = _filter_tide_data(
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
    df = _filter_tide_data(
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
    

def get_tide_clock_file():
    prior_tide = _get_closest_tide('prior')
    prior_tide_time = prior_tide['Timestamp'].iloc[0]
    prior_tide_type = prior_tide['Tide'].iloc[0]
    next_tide = _get_closest_tide('next')
    next_tide_time = next_tide['Timestamp'].iloc[0]
    next_tide_type = next_tide['Tide'].iloc[0]

    length = 12
    time_difference = (next_tide_time - prior_tide_time)/length

    # getting a starting point for the search
    current_time = datetime.now()
    min_dist = current_time - prior_tide_time
    pos = 0

    for i in range(length+1):
        incremented_time = prior_tide_time + time_difference * i
        if abs(current_time - incremented_time) < min_dist:  # min_dist will always be >= 0
            pos = i
            min_dist = abs(current_time - incremented_time)

    if prior_tide_type == 'Low':
        pos += 12
        pos = pos % 24
        
    return f'assets/tide_clock/tideclock_pos_{pos}.png'