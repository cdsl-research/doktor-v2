import os
from datetime import datetime
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient

MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "paper")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/"

client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DBNAME]

app = FastAPI()


class Paper(BaseModel):
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
def create_paper_handler():
    return {
        "id": 1,
        "author_id": [2, 5, 8],
        "title": "my second paper",
        "keywords": ["cloud"],
        "categories_id": [3],
        "abstract": "this is a pen.",
        "url": "https://example.com/yyy",
        "thumbnail_url": "https://example.com/zzz",
        "created_at": "1985-06-24T23:20:50.52Z",
        "updated_at": "2021-04-18T23:20:50.52Z",
    }


@app.get("/paper")
def read_papers_handler():
    return [
        {
            "id": 1,
            "author_id": [2, 3, 4],
            "title": "my original paper",
            "keywords": ["cloud", "network"],
            "categories_id": [1, 2],
            "abstract": "this is a paper.",
            "url": "https://example.com/xxx",
            "thumbnail_url": "https://example.com/zzz",
            "created_at": "1985-07-12T23:20:50.52Z",
            "updated_at": "2021-05-12T23:20:50.52Z",
        },
        {
            "id": 2,
            "author_id": [2, 5, 8],
            "title": "my second paper",
            "keywords": ["cloud"],
            "categories_id": [3],
            "abstract": "this is a pen.",
            "url": "https://example.com/yyy",
            "thumbnail_url": "https://example.com/zzz",
            "created_at": "1985-06-24T23:20:50.52Z",
            "updated_at": "2021-04-18T23:20:50.52Z",
        }
    ]


@app.get("/paper/{paper_id}")
def read_paper_handler(paper_id: int):
    my_paper = {
        "id": str(paper_id),
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
    return Paper(**my_paper)


@app.put("/paper/{paper_id}")
def update_paper_handler(paper_id: int):
    return {
        "id": str(paper_id),
        "author_id": [2, 5, 8],
        "title": "my second paper",
        "keywords": ["cloud"],
        "categories_id": [3],
        "abstract": "this is a pen.",
        "url": "https://example.com/yyy",
        "thumbnail_url": "https://example.com/zzz",
        "created_at": "1985-06-24T23:20:50.52Z",
        "updated_at": "2021-04-18T23:20:50.52Z",
    }
