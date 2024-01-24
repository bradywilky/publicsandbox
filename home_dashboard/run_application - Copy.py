import os
from datetime import datetime, timedelta
import dash
from dash import html, dcc, dash_table
from pull_tide_predictions import get_future_tides_display_data, get_closest_tide_display_strings
from generate_recorded_data_plot import run_tidal_plot_generation, run_temperature_plot_generation
from pull_weather_data import weather_api_call, pull_hourly_forecast, pull_current_weather

# Define your functions and variables
today = datetime.now()
yesterday = today + timedelta(days=-1)
priorweek = today + timedelta(days=-6)
tomorrow = today + timedelta(days=1)

prior_tide, prior_tide_color_string = get_closest_tide_display_strings(proximity='prior')
next_tide, next_tide_color_string = get_closest_tide_display_strings(proximity='next')

future_tides_display_data = get_future_tides_display_data()

weather_data = weather_api_call()
hourly_forecast = pull_hourly_forecast(weather_data)
current_weather_dict = pull_current_weather(weather_data)

run_tidal_plot_generation(
    begin_date=yesterday.strftime('%Y%m%d'),
    end_date=today.strftime('%Y%m%d'),
)

run_temperature_plot_generation(
    begin_date=priorweek.strftime('%Y%m%d'),
    end_date=today.strftime('%Y%m%d'),
)

# Style conditional
style_data_conditional=[
    {
        'if': {
            'filter_query': '{Future Tides} contains "High"',
            'column_id': 'Future Tides'
        },
        'backgroundColor': 'rgba(255, 0, 0, 0.1)',
        'color': 'black'
    },  
    {
        'if': {
            'filter_query': '{Future Tides} contains "Low"',
            'column_id': 'Future Tides'
        },
        'backgroundColor': 'rgba(0, 0, 255, 0.1)',
        'color': 'black'
    }
]

app = dash.Dash(__name__)

# Define widths for the tables
next_tide_width = '400px'
# Define the layout
app.layout = html.Div(
    style={'display': 'flex', 'flex-direction': 'row'},  # Style for the main Div
    children=[
        # Include Google Font for Roboto
        html.Link(
            href='https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap', 
            rel='stylesheet'
        ),

        # Column 1: Div for images
        html.Div(
            children=[



                # Weather widget
                html.Div(
                    id='weather-widget',
                    children=[
                        html.P(current_weather_dict['location'], style={'fontFamily': 'Roboto', 'fontSize': 20, 'marginTop': '5px', 'marginBottom': '5px'}),
                        html.P(current_weather_dict['temperature'], style={'fontFamily': 'Roboto', 'fontSize': 80, 'marginTop': '5px','marginBottom': '5px'}),
                        html.P(f"{current_weather_dict['description']}, wind {current_weather_dict['wind']}", style={'fontFamily': 'Roboto', 'fontSize': 20, 'marginTop': '5px','marginBottom': '5px'}),
                        html.Div(
                            style={'display': 'flex', 'alignItems': 'center'},  # Use flexbox for horizontal alignment
                            children=[
                                html.Img(src="/assets/static/sunset.png", style={'width': '4%', 'height': '4%', 'marginRight': '5px'}),
                                html.P(f"{current_weather_dict['sunset']}", style={'fontFamily': 'Roboto', 'fontSize': 20, 'marginTop': '0px', 'marginBottom': '0px'}),
                            ]
                        ),                        
                    ],
                    style={'margin-left': '20px', 'fontFamily': 'Roboto'}
                ),
                
                
                
                # Tides/Water Level section
                html.Div(
                    id='tidal',
                    style={
                        'display': 'flex',
                        'flex-direction': 'row'
                    },                    
                    children=[
                        html.Img(src="/assets/water_level.png", style={'width': '100%', 'margin-bottom': '20px'}),
                        html.Div(
                            id='close_tides',
                            style={
                                'display': 'flex',
                                'flex-direction': 'column'
                            },                    
                            children=[                        
                                dash_table.DataTable(
                                    id='table1',
                                    columns=[{"name": "Recent Tide", "id": "Recent Tide"}],
                                    data=[{"Recent Tide": prior_tide}],
                                    style_cell={
                                        'backgroundColor': prior_tide_color_string,
                                        'textAlign': 'left',
                                        'fontFamily': 'Roboto',
                                        'fontSize': 27,
                                        'minWidth': '100px',
                                        'width': '100px',
                                        'maxWidth': next_tide_width,
                                        'overflow': 'hidden',
                                        'textOverflow': 'ellipsis',
                                    },
                                    style_header={
                                        'backgroundColor': 'rgba(0, 0, 0, 0.05)',
                                        'fontWeight': 'bold',
                                        'fontFamily': 'Roboto',
                                        'fontSize': 29,
                                    },
                                    style_table={
                                        'width': next_tide_width,
                                        'maxWidth': next_tide_width
                                    }
                                ),
                                dash_table.DataTable(
                                    id='table2',
                                    columns=[{"name": "Next Tide", "id": "Next Tide"}],
                                    data=[{"Next Tide": next_tide}],
                                    style_cell={
                                        'backgroundColor': next_tide_color_string,
                                        'textAlign': 'left',
                                        'fontFamily': 'Roboto',
                                        'fontSize': 27,
                                        'minWidth': '100px',
                                        'width': '100px',
                                        'maxWidth': next_tide_width,
                                        'overflow': 'hidden',
                                        'textOverflow': 'ellipsis',
                                    },
                                    style_header={
                                        'backgroundColor': 'rgba(0, 0, 0, 0.05)',
                                        'fontWeight': 'bold',
                                        'fontFamily': 'Roboto',
                                        'fontSize': 29,
                                    },
                                    style_table={
                                        'width': next_tide_width,
                                        'maxWidth': next_tide_width
                                    }
                                )
                            ]
                        )
                    ]
                ),
                    
                html.Img(src="/assets/watertemp.png", style={'width': '100%'}),
            ],
            style={
                'display': 'flex',
                'flex-direction': 'column',
                'margin-right': '20px'
            }
        ),
        
        # Column 2: Div for the first two tables
        html.Div(
            style={
                'display': 'flex',
                'flex-direction': 'column',
                'margin-right': '60px'
            },
            children=[
                # Container div for first table

                # Container div for second table
                html.Div(
                    children=[

                    ],
                    style={'margin-bottom': '20px'}
                )
            ]
        ),
        
        # Column 3: Div for the third table and weather widget
        html.Div(
            style={
                'display': 'flex',
                'flex-direction': 'column'
            },
            children=[
                # Container div for third table
                html.Div(
                    children=[
                        dash_table.DataTable(
                            id='tb_future_tides',
                            columns=[{"name": i, "id": i} for i in future_tides_display_data.columns],
                            data=future_tides_display_data.to_dict('records'),
                            style_data_conditional=style_data_conditional,
                            style_cell={
                                'textAlign': 'left',
                                'fontFamily': 'Roboto',
                                'fontSize': 16,
                                'minWidth': '10px',
                                'width': '150px',
                                'maxWidth': '250px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            },
                            style_header={
                                'backgroundColor': 'rgba(0, 0, 0, 0.05)',
                                'fontWeight': 'bold',
                                'fontFamily': 'Roboto',
                                'fontSize': 20,
                            },
                            style_table={
                                'width': '250px',
                                'maxWidth': '250px'
                            }
                        )
                    ],
                    style={'margin-bottom': '20px'}
                ),
            ]
        )
    ]
)


if __name__ == '__main__':
    app.run_server(debug=True)
