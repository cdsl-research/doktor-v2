from asyncore import write
from distutils.file_util import write_file
import os
import socket
import time
from typing import List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import requests

""" Paper Service """
PAPER_SVC_HOST = os.getenv("PAPER_SVC_HOST", "paper-app:8000")

""" Elasticsearch Setup """
ELASTICSEARCH_HOST = os.getenv(
    "ELASTICSEARCH_HOST", "fulltext-elasticsearch:9000")

""" FastAPI Setup """
app = FastAPI()


# class ThumbnailCreateUpdate(BaseModel):
#     paper_uuid: List[UUID]
#     paper_pdf_url: str


# class ThumbnailRead(BaseModel):
#     paper_uuid: UUID
#     thumbnail_url: List[str]
#     is_public: bool


@app.get("/")
def root_handler():
    return {"name": "fulltext"}


@app.get("/healthz")
def healthz_handler():
    return {"status": "ok", "message": "it works"}


@app.get("/topz")
def topz_handler():
    return {"resource": "busy"}


@app.post("/fulltext/{paper_uuid}")
def create_fulltext(paper_uuid: UUID):
    # ファイルの取得
    try:
        file_url = f"http://{PAPER_SVC_HOST}/paper/{paper_uuid}/download"
        print("Fetch url:", file_url)
        pdf_data = requests.get(file_url)
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Cloud not downloads the file.")

    return {"status": "ok"}


@app.get("/fulltext/{paper_uuid}")
def read_fulltext(paper_uuid: UUID):
    pass


if __name__ == "__main__":
    for _ in range(120):
        try:
            res = socket.getaddrinfo(ELASTICSEARCH_HOST, None)
            break
        except Exception as e:
            print("Retry resolve host:", e)
            time.sleep(1)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0")
