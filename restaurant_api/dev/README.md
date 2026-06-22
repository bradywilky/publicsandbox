### Docker
The goal is that anyone should be able to download the code and run it. But most of the time on some rando's computer they dont have Python or the python libraries necessary. So you want to also somehow make sure those are there. The normal way to do that is to create a `container`.

How do you create a `container`? You define it with a `Dockerfile`. It's a file that has its own language and is just named "Dockerfile".

You use these Dockerfile keywords + arguments to define stuff like this:

FROM:
    What image to start from (e.g. a machine that already has Python 3.12 installed)

WORKDIR:
    Inside the container, create/use a folder called (whatever the argument is), and run future commands from there

COPY:
    Bring files from your laptop into the container

RUN:
    Run a command while building the container
    (e.g. pip install -r requirements.txt)

EXPOSE:
    Document that the application inside the container listens on a particular port
    (e.g. 8000 for a FastAPI app)

CMD:
    The command that should run when the container starts
    (e.g. uvicorn app.main:app --host 0.0.0.0 --port 8000)


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
