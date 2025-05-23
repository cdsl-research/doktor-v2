import os
import sys
from datetime import datetime
from email import message
from http.client import HTTPException
from ipaddress import IPv4Address
from turtle import down
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "stats")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/?uuidRepresentation=pythonLegacy"

client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DBNAME]

app = FastAPI()


class ServiceHello(BaseModel):
    name: str


class ServiceHealth(BaseModel):
    resouce: str


class StatusResponse(BaseModel):
    status: Literal["ok", "error"]
    message: Optional[str] = ""


class StatsCreateUpdate(BaseModel):
    paper_uuid: UUID
    ip_v4_addr: IPv4Address
    timestamp: datetime


class StatsCount(BaseModel):
    paper_uuid: UUID
    total_downloads: int


class StatsCountSeveral(BaseModel):
    stats: List[StatsCount]


@app.get("/", response_model=ServiceHello)
def root_handler():
    return ServiceHello(name="stats")


@app.get("/healthz", response_model=StatusResponse)
def healthz_handler():
    return StatusResponse(status="ok", message="it works")


@app.get("/topz", response_model=ServiceHealth)
def topz_handler():
    return ServiceHealth(resource="busy")


@app.get("/stats", response_model=StatsCountSeveral)
def read_stats_handler():
    query = [
        {
            "$group": {"_id": "$paper_uuid", "total_downloads": {"$sum": 1}},
        },
        {"$sort": {"total_downloads": -1}},
    ]
    print("All Stats Query:", query)
    try:
        downloads = db["stats"].aggregate(query)
        res = []
        for x in list(downloads):
            sc = StatsCount(
                paper_uuid=x["_id"],
                total_downloads=x["total_downloads"])
            res.append(sc)
        return StatsCountSeveral(stats=res)
    except Exception:
        raise HTTPException(status_code=500, detail="Fail to select")


@app.post("/stats", response_model=StatusResponse)
def create_stats_handler(stats: StatsCreateUpdate):
    json_stats = jsonable_encoder(stats)
    my_stats = {
        "paper_uuid": json_stats.get("paper_uuid"),
        "ip_v4_addr": str(json_stats.get("ip_v4_addr")),
        "timestamp": datetime.now(),
    }
    try:
        insert_id = db["stats"].insert_one(my_stats).inserted_id
        print("insert_id:", insert_id)
        return StatusResponse(status="ok",
                              message=f"Success insert = {insert_id}")
    except Exception:
        raise HTTPException(status_code=500, detail="Fail to insert")


@app.get("/stats/{paper_id}", response_model=StatsCount)
def read_stat_handler(paper_id: UUID):
    query = {"paper_uuid": str(paper_id)}
    print("Stats Query:", query)
    try:
        downloads = db["stats"].count_documents(query)
        return StatsCount(paper_uuid=paper_id, total_downloads=downloads)
    except Exception:
        raise HTTPException(status_code=500, detail="Fail to select")


if __name__ == "__main__":
    try:
        client.admin.command("ping")
        print("MongoDB connected.")
    except (ConnectionFailure, OperationFailure) as e:
        print("MongoDB not available. ", e)
        sys.exit(-1)

    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
