import os
from datetime import datetime, timedelta
import dash
from dash import html, dcc, dash_table

from preprocess_tide_data import get_closest_tide_display_strings, get_future_tides_display_data, get_tide_clock_display_config
from generate_recorded_data_plot import run_tidal_plot_generation
from utils.utils import get_color


MAIN_WIDTH = 950
MAIN_HEIGHT = 1100


def get_tide_clock_widget():

    clock_display_conf = get_tide_clock_display_config()
    clock_image_filepath = clock_display_conf['filename']
    tide_to_display = clock_display_conf['tide_to_display']

    # used in _get_time_P function
    RELATIVE_TIDES_DISPLAY_STRINGS = get_closest_tide_display_strings()
    
    
    def _get_time_P(tide_key):
        next_tide = RELATIVE_TIDES_DISPLAY_STRINGS['next']
        
        # we only want to display the immediate next tide
        if tide_key == next_tide['tide']:
            time_display = next_tide['time']
        else:
            time_display = ''
            
        return html.P(
            time_display, style={'fontSize': 20, 'marginTop': '0px', 'marginBottom': '0px'}
        )
        
        
    clock_image = html.Img(
        src=clock_image_filepath,
        style={'width': '450px', 'height': '450px'}
    )
    
    clock_widget = html.Div(
        style={
            'padding': '20px',           # Adds space inside the box
            'width': '500px',            # Sets the width of the box
            'height': '500px',
        
            'border-radius': '15px', # rounds corners
            'backgroundColor': get_color('widget_minor'),
            'display': 'flex',
            'flex-direction': 'column',
            'alignItems': 'center',
        },
        children=[
            _get_time_P('High'),
            clock_image,
            _get_time_P('Low'),
        ]
    )
    
    return clock_widget


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
        src="/assets/water_level.png", style={
            'width': '900px',
            'height': '500px',
            'margin-bottom': '20px',
            'border-radius': '15px'
        }
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
            'padding': '10px',
            'width': '200px',
            'height': '100px',
            'marginBottom': '20px',
            'backgroundColor': get_color('widget_minor'),
            'border-radius': '15px', # rounds corners
            'display': 'flex',
            'flex-direction': 'row',
            'alignItems': 'center',
        },
        children=[
            html.Img(src=f"/assets/static/{fname}.png", style={'width': '15%', 'height': '48%','marginRight': '25px'}),
            html.Div(
                style={'display': 'flex', 'flex-direction': 'column', 'alignItems': 'center'},
                children=[                    
                    html.P(time, style={'fontSize': 26, 'marginTop': '0px', 'marginBottom': '0px'}),                                
                    html.Div(relative_day, style={'fontSize': 25,})                
                ]
            ),          

        ]
    )
    
    return div
    
def get_future_tide_widget():
    future_tides = get_future_tides_display_data()
    future_tide_children = [get_future_tide_div(i) for i in future_tides]
    future_tides_div = html.Div(
        style={
            'display': 'flex',
            'flex-direction': 'column',
            'marginLeft': '20px',
        },
        children=future_tide_children[:4]
    )
    
    return future_tides_div
    
    

def get_tides_widget():
    return html.Div(
        style={
            'border': '1px solid black',
            'padding': '20px',
            'margin': '10px',
            'width': f'{MAIN_WIDTH}px',
            'height': f'{MAIN_HEIGHT}px',
            'border-radius': '15px',
            'backgroundColor': get_color('widget_main'),
            'display': 'flex',
            'flex-direction': 'column',
        },
        children=[
            html.Div(
                style={'display': 'flex', 'flex-direction': 'row', 'marginBottom': '30px',},
                children=[
                    get_tide_clock_widget(),
                    get_future_tide_widget(),
                ]
            ),
            get_tide_graph_widget(),
        ]
    )