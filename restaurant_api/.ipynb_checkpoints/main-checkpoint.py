# app/main.py

from fastapi import FastAPI

from app.restaurant_service import run

app = FastAPI()


@app.get("/restaurants/open")
def get_open_restaurants(datetime_string):
    return {
        "restaurants": run(datetime_string)
    }