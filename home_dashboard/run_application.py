import dash, argparse
from dash import html, dcc
from dash.dependencies import Input, Output

from get_tides_widget import get_tides_widget
from get_weather_widget import get_weather_widget, get_current_time_widget, get_current_date_widget
from utils.utils import set_background_color


parser = argparse.ArgumentParser(description='Your script description')
parser.add_argument('-l', '--lite', action='store_true', help='run in lite mode')
args = parser.parse_args()

set_background_color()  

args.lite = True
if args.lite:
    datetime_interval = 86400000  # 24 hours in milliseconds
    
else:
    datetime_interval = 60000  # 1 minute in milliseconds

app = dash.Dash(__name__)

app.layout = html.Div(
    style={
        'display': 'flex',
        'flex-direction': 'column',
    },
    children=[
        html.Div(id='weather-widget-container', children=[get_weather_widget(args.lite)]),
        html.Hr(style={'border': '1px solid rgba(0, 0, 255, 0.2)', 'width': '50px', 'margin': '4px 0'}),
        html.Div(id='tides-widget-container', children=[get_tides_widget()]),
        dcc.Interval(
            id='interval-component',
            interval=900000,  # 15 minutes in milliseconds
            n_intervals=0
        ),
        dcc.Interval(
            id='datetime-interval-component',
            interval=datetime_interval,
            n_intervals=0
        )
    ]
)

# per ChatGPT:
# The decorator syntax in Python uses the @ symbol and is considered syntactic sugar.
# It makes your code cleaner and more readable. For example, @my_decorator applied above
# a function definition is just a shorthand for my_function = my_decorator(my_function).

# A callback is supposed to be used like this:
# @app.callback(
    # Output({Element ID to be Updated}, {Parameter of Element to Update}),
    # [Input({Element ID that contains update trigger}, {Parameter of Element that when the value of the parameter changes, the update is triggered})]
 
@app.callback(
    Output('weather-widget-container', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_weather_widget(n):
    return [get_weather_widget(args.lite)]

@app.callback(
    Output('tides-widget-container', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_tides_widget(n):
    return [get_tides_widget()]
    
@app.callback(
    Output('datetime-widget-container', 'children'),
    [Input('datetime-interval-component', 'n_intervals')]
)
def update_datetime_widget(n):
    if args.lite:
        return [get_current_date_widget()]
    return [get_current_time_widget()]    


if __name__ == '__main__':
    app.run_server(debug=True)
