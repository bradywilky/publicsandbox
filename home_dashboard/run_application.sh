# create venv if doesn't exist
python3 -m venv home_dashboard_venv

# activate venv
source home_dashboard_venv/bin/activate

# install all required Python libraries
pip3 install -r requirements.txt

# run app
python3 run_application.py