import os
from datetime import datetime, timedelta
import dash
from dash import html, dcc, dash_table

from get_tide_status_widget import get_tide_graph_widget, get_tide_status_widget, get_future_tide_widget


app = dash.Dash(__name__)

app.layout = html.Div(
    html.Div(
        style={
            'border': '1px solid black',  # Creates a border around the div
            'padding': '20px',           # Adds some space inside the box around the text
            'margin': '10px',            # Adds space outside the box
            'width': '950px',            # Sets the width of the box
            'height': '700px',           # Sets the height of the box
            'box-shadow': '2px 2px 2px lightgrey',  # Optional: adds a shadow effect
            'border-radius': '15px', # rounds corners
            'backgroundColor': 'rgb(51, 122, 158)',
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
)
if __name__ == '__main__':
    app.run_server(debug=True)