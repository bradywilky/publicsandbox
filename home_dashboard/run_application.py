
import schedule
import time
import dash
from dash import html

from get_tides_widget import get_tides_widget
from get_weather_widget import get_weather_widget
from utils.utils import set_background_color


        
        
def job():        
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
        
        
# schedule.every(30).minutes.do(job)

# while True:
    # schedule.run_pending()
    # time.sleep(10)        
    

job()