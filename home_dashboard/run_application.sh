#!/bin/bash

# create venv if doesn't exist
if [ ! -d "home_dashboard_venv" ]; then
    python3 -m venv home_dashboard_venv
fi

# activate venv
source home_dashboard_venv/bin/activate

# install all required Python libraries
pip3 install -r requirements.txt

# check for optional command line argument
if [[ $1 == "lite" ]]; then
    # run lite version of the app
    python3 run_application.py -l
else
    # run full app
    python3 run_application.py
fi