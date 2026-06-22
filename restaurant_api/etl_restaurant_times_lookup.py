import pandas as pd
import re
import json

from deps.constants import DAYS


def get_next_day(day):
    i = DAYS.index(day)
    next_day = DAYS[(i + 1) % len(DAYS)]
    return next_day

def get_days_open_list_from_raw_day_string(days):
    days = days.strip().lower()
    
    days_list = []
    
    day_ranges = [d for d in days.split(',') if '-' in d]
    day_standalones = [d.strip() for d in days.split(',') if '-' not in d]

    for raw_day_range_string in day_ranges:
        first_day = raw_day_range_string.split('-')[0]
        last_day = raw_day_range_string.split('-')[1]
        
        in_range = False
        for D in DAYS+DAYS:
            if first_day.startswith(D):
                in_range = True
            if in_range:
                days_list.append(D)
            if last_day.startswith(D):
                break

    for day in day_standalones:
        for D in DAYS+DAYS:
            if day.startswith(D):
                days_list.append(D)
                break
                
    return set(days_list)

    
def get_open_close_times_from_range(raw_time_range_string):
    raw_time_range_string = raw_time_range_string.strip()
    
    def transform_raw_time(s):
    
        # Look for digits:digits first
        match = re.search(r'(\d+:\d+)', s)
        if match:
            time = match.group(1)
        else:
            # Otherwise find all digits
            digits = ''.join(re.findall(r'\d', s))
            # if len(digits) == 2:
                # time = f'{digits}:00'
            time = f'{digits}:00'
            # else:
            #     return None
    
        hours, minutes = time.split(':')
        hours = int(hours)
    
        if 'pm' in s.lower() and hours != 12:
            hours += 12
    
        if 'am' in s.lower() and hours == 12:
            hours = 0
    
        return f'{hours:02d}:{minutes}'

        
    first_time = raw_time_range_string.split('-')[0]
    last_time = raw_time_range_string.split('-')[1]

    first_time = transform_raw_time(first_time)
    last_time = transform_raw_time(last_time)

    return {
        'open': first_time,
        'close': last_time
    }


def restaurant_lookup_etl(
        csv_filename='deps/restaurants.csv',
        save_json=False,
        save_json_filename='deps/all_restaurants_hours.json'
):
    all_restaurants_hours = {}

    df = pd.read_csv(csv_filename)
    for _, row in df.iterrows():
        
        restaurant_hours = {}
        for D in DAYS:
            restaurant_hours[D] = []
            
        restaurant = row['Restaurant Name']
    
        hours = row['Hours']
        hours = hours.lower()
        for s in hours.split('/'):
            days = re.match(r'^[^\d]*', s).group()
            times = s.replace(days, '').strip()
            
            time_ranges = [t for t in times.split(',') if '-' in t]
            time_range = time_ranges[0]
            days_open = get_days_open_list_from_raw_day_string(days)
            open_close_times = get_open_close_times_from_range(time_range)
            for day in days_open:
                restaurant_hours[day] = [open_close_times]
    
        # correcting for spilling over times
        corrections_to_append = []
        for k in restaurant_hours:
            if restaurant_hours[k]:
                for one_set_of_hours in restaurant_hours[k]:
                    close_time = one_set_of_hours['close']
                    if close_time < one_set_of_hours['open']:
                        restaurant_hours[get_next_day(k)].append({'open': '00:00', 'close': f'{close_time}'})

        for k in restaurant_hours:
            if restaurant_hours[k]:
                for one_set_of_hours in restaurant_hours[k]:
                    if one_set_of_hours['close'] < one_set_of_hours['open']:
                        one_set_of_hours['close'] = '24:00'
            
        all_restaurants_hours[restaurant] = restaurant_hours


    if save_json:
        with open(save_json_filename, 'w') as f:
            f.write(json.dumps(all_restaurants_hours))

    return all_restaurants_hours
