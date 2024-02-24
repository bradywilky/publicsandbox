import dash
from dash import html, dcc
from dash.dependencies import Input, Output

from get_tides_widget import get_tides_widget
from get_weather_widget import get_weather_widget, get_current_time_widget
from utils.utils import set_background_color

set_background_color()  

app = dash.Dash(__name__)

app.layout = html.Div(
    style={
        'display': 'flex',
        'flex-direction': 'column',
    },
    children=[
        html.Div(id='weather-widget-container', children=[get_weather_widget()]),
        html.Hr(style={'border': '1px solid rgba(0, 0, 255, 0.2)', 'width': '50px', 'margin': '4px 0'}),
        html.Div(id='tides-widget-container', children=[get_tides_widget()]),
        dcc.Interval(
            id='interval-component',
            interval=900000,  # 15 minutes in milliseconds
            n_intervals=0
        ),
        dcc.Interval(
            id='time-interval-component',
            interval=60000,  # 1 minute in milliseconds
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
    return [get_weather_widget()]

@app.callback(
    Output('tides-widget-container', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_tides_widget(n):
    return [get_tides_widget()]
    
@app.callback(
    Output('time-widget-container', 'children'),
    [Input('time-interval-component', 'n_intervals')]
)
def update_time_widget(n):
    return [get_current_time_widget()]    


if __name__ == '__main__':
    app.run_server(debug=True)
