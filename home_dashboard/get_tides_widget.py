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
        src="/assets/water_level.png", style={'size': '50%', 'margin-bottom': '20px'}
    )
    
    
def get_tide_status_widget():
    closest_tide_display_strings = get_closest_tide_display_strings()

    box1 = html.Div(
        style={
            'padding': '10px',           # Adds some space inside the box around the text
            'margin': '1px',            # Adds space outside the box
            'width': '180px',            # Sets the width of the box
            'height': '100px',           # Sets the height of the box
            'backgroundColor': get_color('widget_alt1'),
            
            'display': 'flex',
            'flex-direction': 'column',
        },
        children=[
            html.Div(
                'previous',
                style={
                    'marginTop': '0px',
                    'marginBottom': '0px',     
                }
            ),
            html.Div(
                style={'display': 'flex', 'alignItems': 'center'},  # Use flexbox for horizontal alignment
                children=[
                    html.P(closest_tide_display_strings['prior']['tide'], style={'fontSize': 50, 'marginTop': '0px', 'marginBottom': '0px', 'marginRight': '20px'}),            
                    html.Img(src=f"/assets/static/{closest_tide_display_strings['prior']['fname']}.png", style={'width': '10%', 'height': '60%',}),

                ]
            ),          
            html.Div(
                closest_tide_display_strings['prior']['time'],
                style={
                    'fontSize': 25,
                }
            )
        ]
    )

    box2 = html.Div(
        style={
            'padding': '10px',           # Adds some space inside the box around the text
            'margin': '1px',            # Adds space outside the box
            'width': '200px',            # Sets the width of the box
            'height': '100px',           # Sets the height of the box
            'backgroundColor': get_color('widget_alt1'),
            'box-shadow': '0 0 15px rgba(0, 0, 0, 0.5)',
            
            'display': 'flex',
            'flex-direction': 'column',
        },
        children=[
            html.Div(
                'now',
                style={
                }
            ),
            html.Div(
                style={'display': 'flex', 'alignItems': 'center'},  # Use flexbox for horizontal alignment
                children=[
                    html.P(closest_tide_display_strings['current']['tide'], style={'fontSize': 50, 'marginTop': '0px', 'marginBottom': '0px', 'marginRight': '20px'}),            
                    html.Img(src=f"/assets/static/{closest_tide_display_strings['current']['fname']}.png", style={'width': '15%', 'height': '60%',}),

                ]
            ),          
            html.Div(
                style={
                
                
                }
            )
        ]
    )

    box3 = html.Div(
        style={
            'padding': '10px',           # Adds some space inside the box around the text
            'margin': '1px',            # Adds space outside the box
            'width': '180px',            # Sets the width of the box
            'height': '100px',           # Sets the height of the box
            'backgroundColor': get_color('widget_alt1'),
            
            'display': 'flex',
            'flex-direction': 'column',
        },
        children=[
            html.Div(
                'next',
                style={
                    'marginTop': '0px',
                    'marginBottom': '0px',     
                }
            ),
            html.Div(
                style={'display': 'flex', 'alignItems': 'center'},  # Use flexbox for horizontal alignment
                children=[
                    html.P(closest_tide_display_strings['next']['tide'], style={'fontSize': 50, 'marginTop': '0px', 'marginBottom': '0px', 'marginRight': '20px'}),            
                    html.Img(src=f"/assets/static/{closest_tide_display_strings['next']['fname']}.png", style={'width': '10%', 'height': '60%',}),

                ]
            ),          
            html.Div(
                closest_tide_display_strings['next']['time'],
                style={
                    'fontSize': 25,
                }
            )
        ]
    )


    return html.Div(
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
                children=[
                
                    box1,
                    box2,
                    box3
                ]
            )
        ]
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