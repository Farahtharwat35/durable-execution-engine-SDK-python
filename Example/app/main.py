from fastapi import FastAPI

# Create the FastAPI application
app = FastAPI()

# Define a route for the root URL ("/")
@app.get("/")
def hello_world():
    return {"message": "Hello, World! This is a Python app running in Docker with Uvicorn."}