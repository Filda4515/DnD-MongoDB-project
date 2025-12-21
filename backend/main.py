# To run: fastapi dev main.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/status")
def get_status():
    return {"status": "Online", "version": "1.0.0"}
