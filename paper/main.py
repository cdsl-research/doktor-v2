import os
import sys
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "paper")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/"

client = MongoClient(MONGO_CONNECTION_STRING)
try:
    client.admin.command('ping')
    print("MongoDB connected.")
except (ConnectionFailure, OperationFailure) as e:
    print("MongoDB not available. ", e)
    sys.exit(-1)

db = client[MONGO_DBNAME]
app = FastAPI()


class PaperCreateUpdate(BaseModel):
    author_id: List[int]
    title: str
    keywords: List[str]
    label: str
    categories_id: List[int]
    abstract: str
    url: str
    thumbnail_url: str
    is_public: bool


class PaperRead(BaseModel):
    id: int
    author_id: List[int]
    title: str
    keywords: List[str]
    label: str
    categories_id: List[int]
    abstract: str
    url: str
    thumbnail_url: str
    is_public: bool
    created_at: datetime
    updated_at: datetime
    # todo) reference_id: List[int]


@app.get("/")
def root_handler():
    return {"Hello": "World"}


@app.get("/healthz")
def healthz_handler():
    return {"status": "ok", "message": "it works"}


@app.get("/topz")
def topz_handler():
    return {"resource": "busy"}


@app.post("/paper")
def create_paper_handler(paper: PaperCreateUpdate):
    json_paper = jsonable_encoder(paper)
    import random
    my_paper = {
        "id": random.randint(1, 99),
        "author_id": json_paper.get("author_id"),
        "title": json_paper.get("title"),
        "keywords": json_paper.get("keywords"),
        "label": json_paper.get("label"),
        "categories_id": json_paper.get("categories_id"),
        "abstract": json_paper.get("abstract"),
        "url": json_paper.get("url"),
        "thumbnail_url": json_paper.get("thumbnail_url"),
        "is_public": json_paper.get("is_public"),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    insert_id = db["paper"].insert_one(my_paper).inserted_id
    print("insert_id:", insert_id)
    return PaperRead(**my_paper)


@app.get("/paper")
def read_papers_handler():
    return list(db["paper"].find({"is_public": True}, {'_id': 0}))


@app.get("/paper/{paper_id}")
def read_paper_handler(paper_id: int):
    entry = db["paper"].find_one({"id": paper_id, "is_public": True}, {'_id': 0})
    if entry:
        return entry
    else:
        raise HTTPException(status_code=404, detail="Not Found")


@app.put("/paper/{paper_id}")
def update_paper_handler(paper_id: int, paper: PaperCreateUpdate):
    json_paper = jsonable_encoder(paper)
    my_paper = {
        "id": paper_id,
        "author_id": json_paper.get("author_id"),
        "title": json_paper.get("title"),
        "keywords": json_paper.get("keywords"),
        "label": json_paper.get("label"),
        "categories_id": json_paper.get("categories_id"),
        "abstract": json_paper.get("abstract"),
        "url": json_paper.get("url"),
        "thumbnail_url": json_paper.get("thumbnail_url"),
        "is_public": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    return PaperRead(**my_paper)
