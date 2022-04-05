from asyncore import write
from distutils.file_util import write_file
import io
import os
import socket
import sys
import time
import urllib3
from typing import List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response
from minio import Minio, S3Error
from pydantic import BaseModel
import requests
import fitz


""" Minio Setup"""
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_HOST = os.getenv("MINIO_HOST", "thumbnail-minio:9000")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "thumbnail")

try:
    minio_client = Minio(
        MINIO_HOST,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
except (S3Error, urllib3.exceptions.MaxRetryError) as e:
    print(e)
    sys.exit(-1)


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
    # ファイルの取得
    try:
        file_url = f"http://{MINIO_HOST}:9000/paper/{paper_uuid}.pdf"
        pdf_data = requests.get(file_url)
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Cloud not downloads the file.")

    # 画像の取り出し
    write_file_buffer = {}
    with fitz.open(stream=pdf_data.content, filetype="pdf") as doc:
        for p in range(doc.page_count):
            imglist = doc.get_page_images(p)
            for j, img in enumerate(imglist):
                x_ref = img[0]  # xref number
                x_img = doc.extract_image(x_ref)
                x_ext = x_img.get("ext")
                filename = f"{p:02}-{j:02}.{x_ext}"
                write_file_buffer[filename] = x_img.get("image")

    # 画像の書き出し
    for fname, fbody in write_file_buffer.items():
        put_path = os.path.join(f"{paper_uuid}", fname)
        print("put_path =", put_path)
        minio_client.put_object(
            MINIO_BUCKET_NAME, put_path, io.BytesIO(fbody), length=-1, part_size=1000*1024*1024)


@app.get("/thumbnail/{paper_uuid}/{image_id}")
def read_thumbnail(paper_uuid: UUID, image_id: int):
    try:
        obj_path = f"{paper_uuid}/{image_id}.png"
        response = minio_client.get_object(MINIO_BUCKET_NAME, obj_path)
        res = response.read()
        response.close()
        response.release_conn()
        return Response(content=res.read(), media_type="image/png")
    except Exception as e:
        res_status = 503
        res_message = "Internal Error"
        if e.code in ("NoSuchKey", "NoSuchBucket", "ResourceNotFound"):
            res_status = 404
            res_message = "Not Found"
        raise HTTPException(status_code=res_status, detail=res_message)


if __name__ == "__main__":
    for _ in range(120):
        try:
            res = socket.getaddrinfo(MINIO_HOST, None)
            break
        except Exception as e:
            print("Retry resolve host:", e)
            time.sleep(1)

    found = minio_client.bucket_exists(MINIO_BUCKET_NAME)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET_NAME)
    else:
        print("Bucket 'paper' already exists")

    import uvicorn
    uvicorn.run(app, host="0.0.0.0")
