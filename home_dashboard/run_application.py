import dash
from dash import html
from datetime import datetime
from get_tides_widget import get_tides_widget
from get_weather_widget import get_weather_widget


def set_background_color():
    hour = datetime.now().hour
    if 6 <= hour < 18:
        background_color = "rgb(225, 225, 225)"  # Daytime color
    else:
        background_color = "rgb(49, 48, 80)"   # Nighttime color
        
    with open('templates/template_style.css', 'r') as f:
        style_css_template = f.read()
    style_css = style_css_template.replace('BACKGROUND_COLOR_SUB', background_color)
    with open('assets/style.css', 'w') as f:
        f.write(style_css)
        
        
set_background_color()  


app = dash.Dash(__name__)

app.layout = html.Div(
    style={
        'display': 'flex',
        'flex-direction': 'column',
    },
    children=[
        get_weather_widget(),
        html.Hr(style={'border': '1px solid rgba(0, 0, 255, 0.2)', 'width': '50px', 'margin': '4px 0'}),
        get_tides_widget(),

    ]
)
if __name__ == '__main__':
    app.run_server(debug=True)