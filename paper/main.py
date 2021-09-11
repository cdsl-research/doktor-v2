import os
import socket
import sys
import time
import urllib3
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from minio import Minio, S3Error


""" MongoDB Setup """
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "paper")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/"

mongo_client = MongoClient(MONGO_CONNECTION_STRING)
try:
    mongo_client.admin.command('ping')
    print("MongoDB connected.")
except (ConnectionFailure, OperationFailure) as e:
    print("MongoDB not available. ", e)
    sys.exit(-1)
db = mongo_client[MONGO_DBNAME]


""" Minio Setup"""
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minio")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minio123")
MINIO_HOST = os.getenv("MINIO_HOST", "minio:9000")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKEt_NAME", "paper")

for _ in range(120):
    try:
        res = socket.getaddrinfo(MINIO_HOST, None)
        break
    except Exception as e:
        print("Retry resolve host:", e)
        time.sleep(1)

try:
    minio_client = Minio(
        MINIO_HOST,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        secure=False
    )
    found = minio_client.bucket_exists(MINIO_BUCKET_NAME)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET_NAME)
    else:
        print("Bucket 'paper' already exists")
except (S3Error, urllib3.exceptions.MaxRetryError) as e:
    print(e)
    sys.exit(-1)


""" FastAPI Setup """
app = FastAPI()


class PaperCreateUpdate(BaseModel):
    author_uuid: List[UUID]
    title: str
    keywords: List[str]
    label: str
    categories_id: List[int]
    abstract: str
    url: str
    thumbnail_url: str
    is_public: bool


class PaperRead(BaseModel):
    uuid: UUID
    author_uuid: List[UUID]
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
    my_paper = {
        "uuid": uuid4(),
        "author_uuid": json_paper.get("author_uuid"),
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


@app.get("/paper/{paper_uuid}")
def read_paper_handler(paper_uuid: UUID):
    entry = db["paper"].find_one(
        {"uuid": paper_uuid, "is_public": True}, {'_id': 0})
    if entry:
        return entry
    else:
        raise HTTPException(status_code=404, detail="Not Found")


@app.post("/paper/{paper_uuid}/upload")
async def upload_paper_file_handler(paper_uuid: UUID, file: UploadFile = File(...)):
    try:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Invalid Content-Type")

        print(file.file.fileno())
        response = minio_client.put_object(
            MINIO_BUCKET_NAME,
            f"{paper_uuid}.pdf",
            file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type="application/pdf")
        return {"status": "ok"}
        response.close()
        response.release_conn()
    except S3Error as e:
        print("Upload exception: ", e)
        raise HTTPException(status_code=503, detail=str(e.message))


@app.get("/paper/{paper_uuid}/download")
async def download_paper_handler(paper_uuid: UUID):
    try:
        response = minio_client.get_object(
            MINIO_BUCKET_NAME, f"{paper_uuid}.pdf")
        return Response(content=response.read(), media_type="application/pdf")
        response.close()
        response.release_conn()
    except S3Error as e:
        print("Download exception: ", e)
        _status_code = 404 if e.code in (
            "NoSuchKey", "NoSuchBucket", "ResourceNotFound") else 503
        raise HTTPException(status_code=_status_code, detail=str(e.message))


@app.put("/paper/{paper_uuid}")
def update_paper_handler(paper_uuid: UUID, paper: PaperCreateUpdate):
    json_paper = jsonable_encoder(paper)
    my_paper = {
        "uuid": paper_uuid,
        "author_uuid": json_paper.get("author_uuid"),
        "title": json_paper.get("title"),
        "keywords": json_paper.get("keywords"),
        "label": json_paper.get("label"),
        "categories_id": json_paper.get("categories_id"),
        "abstract": json_paper.get("abstract"),
        "url": json_paper.get("url"),
        "thumbnail_url": json_paper.get("thumbnail_url"),
        "is_public": json_paper.get("is_public"),
        "created_at": datetime.now(),  # todo: get stored data
        "updated_at": datetime.now()
    }
    return PaperRead(**my_paper)
