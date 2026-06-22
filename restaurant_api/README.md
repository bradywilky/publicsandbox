### Running in dev
0. Exit current venv
`deactivate`

Create a virtual environment
`python -m venv .venv`

1. Go into your virtual environment
(PowerShell)
`./.venv/Scripts/Activate.ps1`

2. Make sure to install the dependencies
`pip install -r requirements.txt`

3. open up the port and host the API
`uvicorn main:app`

4. run this in browser
`http://localhost:8000/restaurants/open?datetime_string={DATETIME_STRING_HERE}`
ex:
`http://localhost:8000/restaurants/open?datetime_string={2026-06-22T13:30:00}`
