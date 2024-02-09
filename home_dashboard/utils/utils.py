from datetime import datetime

from pull_weather_data import handle_daily_sun


def _get_bounds():
    sun_json = handle_daily_sun()
    for sun in sun_json['sun_list']:
        if datetime.fromtimestamp(sun['date']).date() == datetime.today().date():
            return datetime.fromtimestamp(sun['rise']), datetime.fromtimestamp(sun['set'])
    return None, None


# {description: image file name}
def get_weather_description_image_switch(description):
    switch = {
        'broken clouds': 'partly_cloudy',
        'clear sky': 'clear_skies',
        'few clouds': 'scattered_cloudy',
        'heavy intensity rain': 'heavy_rain',
        'light rain': 'drizzle',
        'light snow': 'snow',
        'moderate rain': 'rain',
        'overcast clouds': 'cloudy',
        'rain and snow': 'winter_mix',
        'scattered clouds': 'partly_cloudy',
        'snow': 'heavy_snow',
        'very heavy rain': 'heavy_rain',
    }
    
    return f"/assets/static/weather_types/{switch[description]}.png"


def convert_rgb_string_to_tuple(rgb_string):
    # Extract the numerical parts of the string and split them into a list
    numbers = rgb_string[rgb_string.find("(")+1:rgb_string.find(")")].split(",")
    
    # Convert each string number to an integer, then divide by 255 to get a float
    return tuple([int(num) / 255 for num in numbers])
    
    
def set_background_color():
    
    day_begin, day_end = _get_bounds()

    if day_begin <= datetime.now() < day_end:
        background_type = 'background-image'
        background_color = 'linear-gradient(to bottom, rgb(82, 163, 189), rgb(216, 238, 238))'
    else:
        background_type = 'background-color'
        background_color = "rgb(12, 12, 20)"   # Nighttime color
        
    with open('templates/template_style.css', 'r') as f:
        style_css_template = f.read()
    style_css = style_css_template.replace('BACKGROUND_COLOR_SUB', background_color)
    style_css = style_css.replace('BACKGROUND_TYPE_SUB', background_type)
    style_css = style_css.replace('FONT_COLOR_SUB', 'rgb(255, 255, 255)')
    with open('assets/style.css', 'w') as f:
        f.write(style_css)
        
           
def get_color(layout, for_matplotlib=False):
 
    day_begin, day_end = _get_bounds()
    color_dict = {}
    
    if day_begin <= datetime.now() < day_end: # Daytime color
        color_dict['widget_main'] = "rgb(255, 255, 255)"
        color_dict['widget_minor'] = "rgb(51, 122, 158)"
        color_dict['accent1'] = "rgb(55, 55, 55)"
        color_dict['accent2'] = "rgb(155, 55, 55)"
        color_dict['widget_alt1'] = "rgb(12, 12, 20)"
        color_dict['widget_alt2'] = "rgb(12, 12, 20)"
    else: # Nighttime color
        color_dict['widget_main'] = "rgb(28, 28, 40)"
        color_dict['widget_minor'] = "rgb(38, 38, 56)"        
        color_dict['accent1'] = "rgb(155, 155, 155)"
        color_dict['accent2'] = "rgb(255, 255, 255)"
        color_dict['widget_alt1'] = "rgb(12, 12, 20)"
        color_dict['widget_alt2'] = "rgb(12, 12, 20)"        
        
    if for_matplotlib:
        return convert_rgb_string_to_tuple(color_dict[layout])
    return color_dict[layout]