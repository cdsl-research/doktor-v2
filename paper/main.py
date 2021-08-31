from typing import Optional

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root_handler():
    return {"Hello": "World"}

@app.get("/healthz")
def health_handler():
    return {"status": "ok", "message": "it works"}

@app.get("/topz")
def top_handler():
    return {"resource": "busy"}

@app.get("/paper")
def read_papers_handler():
    return [
        {
            "id": 1,
            "author_id": [2, 3, 4],
            "title": "my original paper",
            "keywords": ["cloud", "network"],
            "category_id": [1, 2],
            "abstract": "this is a paper.",
            "url": "https://example.com/xxx",
            "created_at": "1985-07-12T23:20:50.52Z",
            "updated_at": "2021-05-12T23:20:50.52Z",
        },
        {
            "id": 2,
            "author_id": [2, 5, 8],
            "title": "my second paper",
            "keywords": ["cloud"],
            "category_id": [3],
            "abstract": "this is a pen.",
            "url": "https://example.com/yyy",
            "created_at": "1985-06-24T23:20:50.52Z",
            "updated_at": "2021-04-18T23:20:50.52Z",
        }
    ]

@app.post("/paper/{id}")
def read_paper_handler():
    return {
        "id": 2,
        "author_id": [2, 5, 8],
        "title": "my second paper",
        "keywords": ["cloud"],
        "category_id": [3],
        "abstract": "this is a pen.",
        "url": "https://example.com/yyy",
        "created_at": "1985-06-24T23:20:50.52Z",
        "updated_at": "2021-04-18T23:20:50.52Z",
    }

