import os
import sys
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "stats")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/"

client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DBNAME]

app = FastAPI()


class StatsCreateUpdate(BaseModel):
    paper_uuid: UUID
    ip_addr: str
    timestamp: datetime


@app.get("/")
def root_handler():
    return {"name": "stats"}


@app.get("/healthz")
def healthz_handler():
    return {"status": "ok", "message": "it works"}


@app.get("/topz")
def topz_handler():
    return {"resource": "busy"}


@app.post("/stats")
def create_stats_handler(stats: StatsCreateUpdate):
    json_stats = jsonable_encoder(stats)
    my_stats = {
        "uuid": json_stats.get("paper_uuid"),
        "ip_addr": json_stats.get("ip_addr"),
        "timestamp": datetime.now(),
    }
    insert_id = db["stats"].insert_one(my_stats).inserted_id
    print("insert_id:", insert_id)
    return {"status": "ok"}


if __name__ == "__main__":
    try:
        client.admin.command('ping')
        print("MongoDB connected.")
    except (ConnectionFailure, OperationFailure) as e:
        print("MongoDB not available. ", e)
        sys.exit(-1)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0")
