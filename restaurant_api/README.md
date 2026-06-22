### Running in dev
0. Exit current venv
`deactivate`

Create a virtual environment
`python -m venv venv`

1. Go into your virtual environment
`source venv/Scripts/activate`

2. Make sure to install the dependencies
`pip install -r requirements.txt`

3. open up the port and host the API
`uvicorn main:app`