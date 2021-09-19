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
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "author")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/"

client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DBNAME]

app = FastAPI()


class AuthorCreateUpdate(BaseModel):
    first_name_ja: str
    middle_name_ja: Optional[str]
    last_name_ja: str
    first_name_en: str
    middle_name_en: Optional[str]
    last_name_en: str
    joined_year: int
    is_graduated: bool


class AuthorRead(BaseModel):
    uuid: UUID
    first_name_ja: str
    middle_name_ja: str
    last_name_ja: str
    first_name_en: str
    middle_name_en: str
    last_name_en: str
    joined_year: int
    is_graduated: bool
    created_at: datetime
    updated_at: datetime


@app.get("/")
def root_handler():
    return {"Hello": "World"}


@app.get("/healthz")
def healthz_handler():
    return {"status": "ok", "message": "it works"}


@app.get("/topz")
def topz_handler():
    return {"resource": "busy"}


@app.post("/author")
def create_author_handler(author: AuthorCreateUpdate):
    json_author = jsonable_encoder(author)
    my_author = {
        "uuid": uuid4(),
        "first_name_ja": json_author.get("first_name_ja"),
        "middle_name_ja": json_author.get("middle_name_ja"),
        "last_name_ja": json_author.get("last_name_ja"),
        "first_name_en": json_author.get("first_name_en"),
        "middle_name_en": json_author.get("middle_name_en"),
        "last_name_en": json_author.get("last_name_en"),
        "joined_year": json_author.get("joined_year"),
        "is_graduated": json_author.get("is_graduated"),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    insert_id = db["author"].insert_one(my_author).inserted_id
    print("insert_id:", insert_id)
    return AuthorRead(**my_author)


@app.get("/author")
def read_authors_handler():
    return list(db["author"].find({}, {'_id': 0}))


@app.get("/author/{author_uuid}")
def read_author_handler(author_uuid: UUID):
    entry = db["author"].find_one({"uuid": author_uuid}, {'_id': 0})
    if entry:
        return entry
    else:
        raise HTTPException(status_code=404, detail="Not Found")


@app.put("/author/{author_uuid}")
def update_author_handler(author_uuid: UUID, author: AuthorCreateUpdate):
    json_author = jsonable_encoder(author)
    my_author = {
        "uuid": author_uuid,
        "first_name_ja": json_author.get("first_name_ja"),
        "middle_name_ja": json_author.get("middle_name_ja"),
        "last_name_ja": json_author.get("last_name_ja"),
        "first_name_en": json_author.get("first_name_en"),
        "middle_name_en": json_author.get("middle_name_en"),
        "last_name_en": json_author.get("last_name_en"),
        "joined_year": json_author.get("joined_year"),
        "is_graduated": json_author.get("is_graduated"),
        "created_at": datetime.now(),  # todo: get stored data
        "updated_at": datetime.now()
    }
    return AuthorRead(**my_author)


if __name__ == "__main__":
    try:
        client.admin.command('ping')
        print("MongoDB connected.")
    except (ConnectionFailure, OperationFailure) as e:
        print("MongoDB not available. ", e)
        sys.exit(-1)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0")
