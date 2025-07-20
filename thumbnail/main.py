import io
import os
import socket
import sys
import time
import logging
from typing import Literal, Optional
from uuid import UUID

import fitz
import requests
import urllib3
from fastapi import FastAPI, HTTPException, Response
from minio import Minio, S3Error
from minio.deleteobjects import DeleteObject
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

""" Paper Service """
PAPER_SVC_HOST = os.getenv("PAPER_SVC_HOST", "paper-app:8000")

""" Minio Setup"""
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_HOST = os.getenv("MINIO_HOST", "thumbnail-minio:9000")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "thumbnail")

# OpenTelemetry TracerProvider の設定
resource = Resource(attributes={"service.name": "thumbnail"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# OTLP Exporter の設定
otlp_exporter = OTLPSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Requests の計装
RequestsInstrumentor().instrument()

try:
    minio_client = Minio(
        MINIO_HOST,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )
except (S3Error, urllib3.exceptions.MaxRetryError) as e:
    logger.error(e)
    sys.exit(-1)


""" FastAPI Setup """
app = FastAPI()

# FastAPI アプリケーションの計装
FastAPIInstrumentor.instrument_app(app)


class ServiceHello(BaseModel):
    name: str


class ServiceHealth(BaseModel):
    resouce: str


class StatusResponse(BaseModel):
    status: Literal["ok", "error"]
    message: Optional[str] = ""


@app.get("/")
def root_handler():
    return {"name": "thumbnail"}


@app.get("/healthz")
def healthz_handler():
    return {"status": "ok", "message": "it works"}


@app.get("/topz")
def topz_handler():
    return {"resource": "busy"}


@app.get("/thumbnail/{paper_uuid}")
def read_thumbnail(paper_uuid: UUID):
    try:
        files = minio_client.list_objects(MINIO_BUCKET_NAME, prefix=f"{paper_uuid}/")
        filenames = [
            f._object_name.replace(f"{paper_uuid}/", "").replace(".png", "")
            for f in files
        ]
        return {"images": filenames}
    except S3Error as e:
        logger.error("Download exception: %s", e)
        _status_code = (
            404 if e.code in ("NoSuchKey", "NoSuchBucket", "ResourceNotFound") else 503
        )
        raise HTTPException(status_code=_status_code, detail=str(e.message))


@app.post("/thumbnail/{paper_uuid}")
def create_thumbnail(paper_uuid: UUID):
    # ファイルの取得
    try:
        file_url = f"http://{PAPER_SVC_HOST}/paper/{paper_uuid}/download"
        logger.info("Fetch url: %s", file_url)
        pdf_data = requests.get(file_url)
    except Exception:
        raise HTTPException(status_code=400, detail="Cloud not downloads the file.")

    # 画像の取り出し
    write_file_buffer = {}
    with fitz.open(stream=pdf_data.content, filetype="pdf") as doc:
        for p in range(doc.page_count):
            imglist = doc.get_page_images(p)
            for j, img in enumerate(imglist):
                x_ref = img[0]  # xref number
                x_img = doc.extract_image(x_ref)
                x_ext = x_img.get("ext")
                filename = f"{p}-{j}.{x_ext}"
                write_file_buffer[filename] = x_img.get("image")

    # 画像の書き出し
    for fname, fbody in write_file_buffer.items():
        put_path = os.path.join(f"{paper_uuid}", fname)
        logger.info("put_path = %s", put_path)
        minio_client.put_object(
            MINIO_BUCKET_NAME,
            put_path,
            io.BytesIO(fbody),
            length=-1,
            part_size=1000 * 1024 * 1024,
        )

    return {"status": "ok"}


@app.get("/thumbnail/{paper_uuid}/{image_id}")
def read_thumbnail(paper_uuid: UUID, image_id: str):
    # todo: image_id の形式のバリデーション
    try:
        obj_path = f"{paper_uuid}/{image_id}.png"
        response = minio_client.get_object(MINIO_BUCKET_NAME, obj_path)
        # response.close()
        return Response(content=response.read(), media_type="image/png")
    except S3Error as e:
        logger.error("Download exception: %s", e)
        _status_code = (
            404 if e.code in ("NoSuchKey", "NoSuchBucket", "ResourceNotFound") else 503
        )
        raise HTTPException(status_code=_status_code, detail=str(e.message))
    except Exception as e:
        res_status = 503
        res_message = "Internal Error"
        logger.error("image fetch error: %s", e)
        raise HTTPException(status_code=res_status, detail=res_message)


@app.delete("/reset", response_model=StatusResponse)
def delete_thumbnail_handler():
    delete_object_list = map(
        lambda x: DeleteObject(x.object_name),
        minio_client.list_objects(MINIO_BUCKET_NAME, recursive=True),
    )
    errors = minio_client.remove_objects(MINIO_BUCKET_NAME, delete_object_list)
    for error in errors:
        logger.error("error occurred when deleting object %s", error)
    return StatusResponse(**{"status": "ok"})


if __name__ == "__main__":
    while True:
        try:
            res = socket.getaddrinfo(MINIO_HOST, None)
            break
        except Exception as e:
            logger.warning("Retry resolve host: %s", e)
            time.sleep(1)

    found = minio_client.bucket_exists(MINIO_BUCKET_NAME)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET_NAME)
    else:
        logger.info("Bucket 'paper' already exists")

    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
