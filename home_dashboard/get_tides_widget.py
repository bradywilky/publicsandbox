import os
from datetime import datetime, timedelta
import dash
from dash import html, dcc, dash_table

from pull_tide_predictions import get_closest_tide_display_strings, get_future_tides_display_data
from generate_recorded_data_plot import run_tidal_plot_generation
from utils.utils import get_color


def get_tide_graph_widget():
    today = datetime.now()
    yesterday = today + timedelta(days=-1)
    try:
        run_tidal_plot_generation(
            begin_date=yesterday.strftime('%Y%m%d'),
            end_date=today.strftime('%Y%m%d'),
        )
    except Exception as e:
        print(f'error generating plot: {e}')

    return html.Img(
        src="/assets/water_level.png", style={'size': '50%', 'margin-bottom': '20px', 'border-radius': '15px'}
    )
    
    
def get_tide_status_widget():
    
    closest_tide_display_strings = get_closest_tide_display_strings()

    def _get_one_tide_status_div(relative_time_key, relative_time_display):

        closest_tide_display_strings = get_closest_tide_display_strings()
        tide = closest_tide_display_strings[relative_time_key]['tide']
        fname = f"/assets/static/{closest_tide_display_strings[relative_time_key]['fname']}.png"
        time = ''
        if relative_time_key != 'current':
            time = closest_tide_display_strings[relative_time_key]['time']
        
        return html.Div(
            style={
                'padding': '10px',
                'margin': '1px',
                'width': '180px',
                'height': '100px',
                'backgroundColor': get_color('widget_alt1'),
                
                'display': 'flex',
                'flex-direction': 'column',
            },
            children=[
                html.Div(relative_time_display, style={'marginTop': '0px', 'marginBottom': '0px',}),
                html.Div(
                    style={'display': 'flex', 'alignItems': 'center'},
                    children=[
                        html.P(tide, style={'fontSize': 50, 'marginTop': '0px', 'marginBottom': '0px', 'marginRight': '20px'}),            
                        html.Img(src=fname, style={'width': '10%', 'height': '60%',}),
                    ]
                ),          
                html.Div(time, style={'fontSize': 25,})
            ]
        )


    status_widgets_info = [
        {'relative_time': 'prior', 'display': 'previous'},
        {'relative_time': 'current', 'display': 'now'},
        {'relative_time': 'next', 'display': 'next'}
    ]
    
    return html.Div(
        style={'display': 'flex', 'flex-direction': 'row',},
        children=[_get_one_tide_status_div(i['relative_time'], i['display']) for i in status_widgets_info]
    )
    
    
def get_future_tide_div(future_tide_dict):
    fname = future_tide_dict['fname']
    time = future_tide_dict['time']
    relative_day = future_tide_dict['relative_day']

    div = html.Div(
        style={
            'padding': '10px',           # Adds some space inside the box around the text
            'margin': '1px',            # Adds space outside the box
            'width': '90px',            # Sets the width of the box
            'height': '30px',           # Sets the height of the box
            'backgroundColor': get_color('widget_minor'),
            'border-radius': '3px', # rounds corners
            'display': 'flex',
            'flex-direction': 'row',
            'alignItems': 'center',
        },
        children=[
            html.Img(src=f"/assets/static/{fname}.png", style={'width': '15%', 'height': '48%','marginRight': '5px'}),
            html.Div(
                style={'display': 'flex', 'flex-direction': 'column', 'alignItems': 'center'},
                children=[                    
                    html.P(time, style={'fontSize': 16, 'marginTop': '0px', 'marginBottom': '0px'}),                                
                    html.Div(relative_day, style={'fontSize': 15,})                
                ]
            ),          

        ]
    )
    
    return div
    
def get_future_tide_widget():
    future_tides = get_future_tides_display_data()
    future_tide_children = [get_future_tide_div(i) for i in future_tides]
    future_tides_div = html.Div(
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
                children=future_tide_children
            )
        ]
    )
    
    return future_tides_div
    
    

def get_tides_widget():
    return html.Div(
        style={
            'border': '1px solid black',  # Creates a border around the div
            'padding': '20px',           # Adds some space inside the box around the text
            'margin': '10px',            # Adds space outside the box
            'width': '950px',            # Sets the width of the box
            'height': '700px',           # Sets the height of the box
        
            'border-radius': '15px', # rounds corners
            'backgroundColor': get_color('widget_main'),
            'display': 'flex',
            'flex-direction': 'column',
        },
        children=[
            get_tide_graph_widget(),
            get_tide_status_widget(),
            html.P('Next Tides', style={'fontSize': 20, 'marginTop': '0px', 'marginBottom': '2px'}),
            get_future_tide_widget(),
        ]
    )