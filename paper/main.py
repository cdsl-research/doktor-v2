from fastapi import FastAPI
from pymongo import MongoClient
import os

MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "paper")
MONGO_URL = os.getenv("MONGO_URL", "mongo:27017")
MONGO_CONNECTION_STRING = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_URL}/"

client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DBNAME]
mongo_collections = db.get_collection()

app = FastAPI()


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
