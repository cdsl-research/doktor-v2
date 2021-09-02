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
    created_at: datetime
    updated_at: datetime


@app.get("/")
def root_handler():
    mongo_collections = db
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
    return PaperRead(**my_paper)


@app.get("/paper")
def read_papers_handler():
    my_paper = {
        "id": 22,
        "author_id": [2, 5],
        "title": "分散トレーシングのためのログ検索の高速化",
        "keywords": ["分散", "トレーシング", "ログ", "検索", "高速化"],
        "label": "CDSL-TR-051",
        "categories_id": [3],
        "abstract": "分散トレーシングは,マイクロサービスアーキテクチャでログによる動作の解析を実現する...",
        "url": "https://drive.google.com/file/d/1feZlqWejgqf8zpWQBQOSpr5JXYkPQL4t/view",
        "thumbnail_url": "https://example.com/zzz",
        "created_at": datetime(1985, 6, 24, 23, 50, 52),
        "updated_at": datetime(2021, 2, 4, 13, 52, 22)
    }
    return [PaperRead(**my_paper), PaperRead(**my_paper)]


@app.get("/paper/{paper_id}")
def read_paper_handler(paper_id: int):
    my_paper = {
        "id": paper_id,
        "author_id": [2, 5],
        "title": "分散トレーシングのためのログ検索の高速化",
        "keywords": ["分散", "トレーシング", "ログ", "検索", "高速化"],
        "label": "CDSL-TR-051",
        "categories_id": [3],
        "abstract": "分散トレーシングは,マイクロサービスアーキテクチャでログによる動作の解析を実現する...",
        "url": "https://drive.google.com/file/d/1feZlqWejgqf8zpWQBQOSpr5JXYkPQL4t/view",
        "thumbnail_url": "https://example.com/zzz",
        "created_at": datetime(1985, 6, 24, 23, 50, 52),
        "updated_at": datetime(2021, 2, 4, 13, 52, 22)
    }
    return PaperRead(**my_paper)


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
