from dateutil import parser

from etl_restaurant_times_lookup import restaurant_lookup_etl


def run(datetime_string):
    dt = parser.parse(datetime_string)
    day_of_week = dt.strftime("%A").lower()
    time_str = dt.strftime("%H:%M")
    all_restaurants_hours = restaurant_lookup_etl()
    
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
