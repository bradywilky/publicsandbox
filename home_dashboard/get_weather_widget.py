import os
from datetime import datetime, timedelta
import dash
from dash import html, dcc, dash_table

from pull_weather_data import weather_api_call, pull_daily_forecast, pull_hourly_forecast, pull_current_weather
from utils.utils import get_color, get_weather_description_image_switch

today = datetime.now()
yesterday = today + timedelta(days=-1)
priorweek = today + timedelta(days=-6)
tomorrow = today + timedelta(days=1)

weather_data = weather_api_call()
daily_forecast_list = pull_daily_forecast(weather_data)
hourly_forecast_list = pull_hourly_forecast(weather_data)
current_weather_dict = pull_current_weather(weather_data)


def get_current_weather_widget():

    return html.Div(
        id='weather-widget',
        style={
            'margin': '20px',
            'width': '300px',            # Sets the width of the box
            'height': '300px',           # Sets the height of the box            
            'display': 'flex',
            'flex-direction': 'column',
            'alignItems': 'center',
            'backgroundColor': get_color('widget_minor'),
            'border-radius': '15px',
        },
        children=[
            html.P(current_weather_dict['location'], style={'fontSize': 20, 'marginTop': '5px', 'marginBottom': '5px'}),
            html.Img(
                src=get_weather_description_image_switch(current_weather_dict['description']),
                style={'object-fit': 'contain', 'max-width': '40%', 'max-height': '40%'}
            ),
            html.P(current_weather_dict['temperature'], style={'fontSize': 100, 'marginTop': '5px','marginBottom': '5px'}),
            html.P(current_weather_dict['wind'], style={'fontSize': 20, 'marginTop': '5px','marginBottom': '16px'}),
            html.Div(
                style={'display': 'flex', 'flex-direction': 'row',},  # Use flexbox for horizontal alignment
                children=[
                    html.Img(src="/assets/static/sunset.png", style={'object-fit': 'contain', 'max-width': '100%', 'max-height': '100%'}),
                    html.Div(current_weather_dict['sunset'], style={'fontSize': 20, 'width': '80px',}),
                ]
            ),                        
        ],
        
    )
    
    
def get_hourly_weather_div(hourly_weather_dict):
    temperature = hourly_weather_dict['temperature']
    wind = hourly_weather_dict['wind']
    weather = hourly_weather_dict['weather']
    time = hourly_weather_dict['time']

    div = html.Div(
        style={
            'padding': '3px',           # Adds some space inside the box around the text
            'margin': '1px',            # Adds space outside the box
            'width': '70px',            # Sets the width of the box
            'height': '117px',           # Sets the height of the box
            'backgroundColor': get_color('widget_minor'),
            
            'display': 'flex',
            'flex-direction': 'column',
            'alignItems': 'center',
        },
        children=[
            html.Img(
                src=get_weather_description_image_switch(weather),
                style={'object-fit': 'contain', 'max-width': '50%', 'max-height': '50%'}
            ),
            html.P(temperature, style={'fontSize': 17, 'marginTop': '3px', 'marginBottom': '2px'}),
            html.P(wind, style={'fontSize': 9, 'marginTop': '0px', 'marginBottom': '0px'}),            
            html.Hr(style={'border': f'1px solid {get_color("accent2")}', 'width': '50px', 'margin': '10px 0'}),
            html.P(time, style={'fontSize': 13, 'fontWeight': 'bold', 'marginTop': '2px', 'marginBottom': '0px'}),
        ]
    )
    
    return div
    
def get_hourly_weather_widget():
    hourly_weather_children = [get_hourly_weather_div(i) for i in hourly_forecast_list]
    hourly_weather_div = html.Div(
        children = [
           # Include Google Font for Roboto
            html.Link(
                href='https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap', 
                rel='stylesheet'
            ),    
            html.Div(
                style={
                    'display': 'flex',
                    'flex-direction': 'row',
                },
                children=hourly_weather_children
            )
        ]
    )
    
    return hourly_weather_div
    
    
def get_daily_weather_div(daily_weather_dict):
    high = daily_weather_dict['hightemp']
    low = daily_weather_dict['lowtemp']
    wind = daily_weather_dict['wind']
    weather = daily_weather_dict['weather']
    day = daily_weather_dict['day']
    date = daily_weather_dict['date']
    

    div = html.Div(
        style={

            'padding': '3px',           # Adds some space inside the box around the text
            'margin': '3px',            # Adds space outside the box
            'width': '120px',            # Sets the width of the box
            'height': '120px',           # Sets the height of the box
            'backgroundColor': get_color('widget_minor'),
            'border-radius': '4px', # rounds corners            
            'display': 'flex',
            'flex-direction': 'column',
            'alignItems': 'center',
        },
        children=[
            html.P(day, style={'fontSize': 18, 'fontWeight': 'bold', 'marginTop': '2px', 'marginBottom': '0px'}),    
            html.P(date, style={'fontSize': 15, 'marginTop': '13px', 'marginBottom': '0px'}),
            html.Hr(style={'border': '1px solid rgba(0, 0, 255, 0.2)', 'width': '50px', 'margin': '4px 0'}),
            html.P(weather, style={'fontSize': 9, 'marginTop': '0px', 'marginBottom': '0px'}),            
            html.P(wind, style={'fontSize': 9, 'marginTop': '0px', 'marginBottom': '0px'}),             
            html.Div(
                style={'display': 'flex', 'flex-direction': 'row', 'alignItems': 'center',},
                children=[
                    html.P(high, style={'fontSize': 22, 'fontWeight': 'bold', 'marginTop': '0px', 'marginBottom': '2px', 'marginRight': '3px',}),
                    html.P(low, style={'fontSize': 14, 'marginTop': '0px', 'marginBottom': '2px',}),
                ]
            ),
        ]
    )
    
    return div
    
def get_daily_weather_widget():
    daily_weather_children = [get_daily_weather_div(i) for i in daily_forecast_list]
    daily_weather_div = html.Div(
        children = [
           # Include Google Font for Roboto
            html.Link(
                href='https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap', 
                rel='stylesheet'
            ),    
            html.Div(
                style={
                    'display': 'flex',
                    'flex-direction': 'row',
                },
                children=daily_weather_children
            )
        ]
    )
    
    return daily_weather_div
    
    
def get_weather_widget():
    return html.Div(
        style={

            'padding': '20px',           # Adds some space inside the box around the text
            'margin': '10px',            # Adds space outside the box
            'width': '950px',            # Sets the width of the box
            'height': '700px',           # Sets the height of the box
            'border-radius': '15px', # rounds corners
            'backgroundColor': get_color('widget_main'),
            'display': 'flex',
            'flex-direction': 'column',
            'box-shadow': '0 0 15px rgba(0, 0, 0, 0.5)',
        },
        children=[

            html.Div(
                style={'display': 'flex', 'flex-direction': 'row', 'marginBottom': '100px'},
                children=[
                    get_current_weather_widget(),                    
                    get_hourly_weather_widget(),
                ]
            ),
            get_daily_weather_widget(),            
        ]
    )