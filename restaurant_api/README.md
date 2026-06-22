Run these to start the app from the Dockerfile.

```
docker build -t restaurant-api .
docker run -p 8000:8000 restaurant-api
```

Example request:
`http://localhost:8000/restaurants/open?datetime_string=2026-06-22T13:30:00`