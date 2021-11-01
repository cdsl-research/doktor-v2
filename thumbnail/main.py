import os
import socket
import time
from typing import List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

import minio_manager


""" Minio Setup"""
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_HOST = os.getenv("MINIO_HOST", "minio:9000")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "thumbnail")

""" FastAPI Setup """
app = FastAPI()


class ThumbnailCreateUpdate(BaseModel):
    paper_uuid: List[UUID]
    paper_pdf_url: str


class ThumbnailRead(BaseModel):
    paper_uuid: UUID
    thumbnail_url: List[str]
    is_public: bool


@app.get("/")
def root_handler():
    return {"name": "thumbnail"}


@app.get("/healthz")
def healthz_handler():
    return {"status": "ok", "message": "it works"}


@app.get("/topz")
def topz_handler():
    return {"resource": "busy"}


@app.post("/thumbnail/{paper_uuid}")
def create_thumbnail(paper_uuid: UUID):
    import pdf2png
    folder = pdf2png.thumbnail(f"http://minio:9000/paper/{paper_uuid}.pdf")
    # try:
    result = minio_manager.upload_local_directory_to_minio(
        folder, bucket_name="thumbnail", minio_path=f"{paper_uuid}/")
    return result
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=e)


@app.get("/thumbnail/{paper_uuid}")
def read_thumbnail(paper_uuid: UUID):
    # try:
    res = minio_manager.download_paper_handler(paper_uuid)
    return Response(content=res, media_type="image/png")

    # except:
    #     raise HTTPException(status_code=status_code, detail=str(e.message))


@app.put("/thumbnail/{paper_uuid}")
def update_paper_handler(paper_uuid: UUID, paper: ThumbnailCreateUpdate):
    pass


if __name__ == "__main__":
    for _ in range(120):
        try:
            res = socket.getaddrinfo(MINIO_HOST, None)
            break
        except Exception as e:
            print("Retry resolve host:", e)
            time.sleep(1)

    minio_manager.initialize()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0")
