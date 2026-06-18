import json
from dateutil import parser

def run(datetime_string):
    dt = parser.parse(datetime_string)
    day_of_week = dt.strftime("%A").lower()
    time_str = dt.strftime("%H:%M")
    with open('../deps/RESTAURANTS_HOURS.json', 'r') as f:
        all_restaurants_hours = json.loads(f.read())
    
    open_restaurants = []
    for restaurant in all_restaurants_hours:
        
        one_restaurant_hours = all_restaurants_hours[restaurant]
        hours_set = None
        
        for day_key in one_restaurant_hours:
            if day_of_week.startswith(day_key):
                hours_set = one_restaurant_hours[day_key]
                break
        
        if hours_set:
            for hours in hours_set:
                if time_str >= hours['open'] and time_str <= hours['close']:
                    open_restaurants.append(restaurant)

    return open_restaurants