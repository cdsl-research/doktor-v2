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

import pdf2png


""" Minio Setup"""
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_HOST = os.getenv("MINIO_HOST", "minio:9000")
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


def _download_paper_from_minio(paper_uuid):
    try:
        response = minio_client.get_object(
            MINIO_BUCKET_NAME, f"{paper_uuid}-00.png")
        res = response.read()
        response.close()
        response.release_conn()
        return res

    except S3Error as e:
        print("Download exception: ", e)
        _status_code = 404 if e.code in (
            "NoSuchKey", "NoSuchBucket", "ResourceNotFound") else 503
        return _status_code, e


def upload_local_directory_to_minio(local_dir, minio_bucket_name, minio_path):
    import glob
    assert os.path.isdir(local_dir)

    for local_file in glob.glob(local_dir + '/**'):
        local_file = local_file.replace(
            os.sep, "/")  # Replace \ with / on Windows
        if not os.path.isfile(local_file):
            upload_local_directory_to_minio(
                local_file,
                minio_bucket_name,
                minio_path +
                "/" +
                os.path.basename(local_file))
        else:
            remote_path = os.path.join(
                minio_path, local_file[1 + len(local_dir):])
            remote_path = remote_path.replace(
                os.sep, "/")  # Replace \ with / on Windows
            minio_client.fput_object(
                minio_bucket_name, remote_path, local_file)


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
    file_url = f"http://{MINIO_HOST}:9000/paper/{paper_uuid}.pdf"
    try:
        stored_path, stored_filename = pdf2png.fetch_pdf_http(file_url)
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Cloud not downloads the file.")

    created_files = pdf2png.convert_pdf_to_png(stored_path, stored_filename)
    # created_files_fullpath = [os.path.join(stored_path, f) for f in created_files]
    upload_local_directory_to_minio(
        stored_path, bucket_name="thumbnail", minio_path=f"{paper_uuid}/")


@app.get("/thumbnail/{paper_uuid}/{image_id}")
def read_thumbnail(paper_uuid: UUID, image_id: int):
    try:
        res = _download_paper_from_minio(paper_uuid)
        return Response(content=res, media_type="image/png")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Error")


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
