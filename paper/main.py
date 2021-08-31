from typing import Optional

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def top_handler():
    return {"Hello": "World"}
