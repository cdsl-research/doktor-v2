import io
import logging
import os
import socket
import sys
import time
from contextlib import asynccontextmanager
from typing import Literal, Optional
from uuid import UUID

import fitz
import requests
import urllib3
from fastapi import FastAPI, HTTPException, Response
from minio import Minio, S3Error
from minio.deleteobjects import DeleteObject
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import \
    OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAPER_SVC_HOST = os.getenv("PAPER_SVC_HOST", "paper-app:8000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_HOST = os.getenv("MINIO_HOST", "thumbnail-minio:9000")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "thumbnail")

# =============================================================================
# OpenTelemetry setup
# =============================================================================

resource = Resource(
    attributes={"service.name": os.getenv("OTEL_SERVICE_NAME", "thumbnail")}
)

# Setup TracerProvider
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# Setup OTLP Span Exporter
otlp_span_exporter = OTLPSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_span_exporter))

# Setup LoggerProvider
logger_provider = LoggerProvider()
set_logger_provider(logger_provider)

# Setup OTLP Log Exporter
otlp_log_exporter = OTLPLogExporter()
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(otlp_log_exporter))

# Setup LoggingHandler
# Integrate Python's standard logging library with OpenTelemetry
# This allows logging.info() calls to be sent in OTLP format
otlp_handler = LoggingHandler(
    level=logging.NOTSET, logger_provider=logger_provider  # Handle all log levels
)

# Add OTLP handler to root logger
# This allows all application logs to be sent in OTLP format
logging.getLogger().addHandler(otlp_handler)

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動時にMinIOバケットを確認・作成"""
    while True:
        try:
            socket.getaddrinfo(MINIO_HOST.split(":")[0], None)
            break
        except Exception as e:
            logger.warning("Retry resolve host: %s", e)
            time.sleep(1)

    found = minio_client.bucket_exists(MINIO_BUCKET_NAME)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET_NAME)
    else:
        logger.info("Bucket '%s' already exists", MINIO_BUCKET_NAME)
    yield


""" FastAPI Setup """
app = FastAPI(lifespan=lifespan)

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
        files = minio_client.list_objects(
            MINIO_BUCKET_NAME, prefix=f"{paper_uuid}/")
        filenames = [
            f._object_name.replace(f"{paper_uuid}/", "").replace(".png", "")
            for f in files
        ]
        return {"images": filenames}
    except S3Error as e:
        logger.error("Download exception: %s", e)
        _status_code = (
            404 if e.code in (
                "NoSuchKey",
                "NoSuchBucket",
                "ResourceNotFound") else 503)
        raise HTTPException(status_code=_status_code, detail=str(e.message))


def _extract_image_as_png(doc: fitz.Document, img: tuple) -> bytes:
    """PDFの埋め込み画像をPNGバイト列として取り出す。

    PDFの画像は本体画像とソフトマスク(smask: 透過情報)が別オブジェクトに
    分かれて格納されることがある。透過すべき領域は本体画像側では黒で埋められ、
    smaskが「どこが透明か」を持つ。smaskを無視して本体画像だけを取り出すと
    透過領域が黒く残ってしまう(issue #353)。

    そのためsmaskが存在する場合は本体画像へalphaチャンネルとして合成する。
    また配信側(read_thumbnail)は常に.pngを読むため、出力はPNGへ統一する。

    img は doc.get_page_images() が返すタプルで、
    img[0]=本体画像のxref, img[1]=smaskのxref(なければ0)。
    """
    xref = img[0]
    smask = img[1]

    # smaskあり: 本体画像にalphaとして合成する
    if smask > 0:
        base = fitz.Pixmap(doc.extract_image(xref)["image"])
        if base.alpha:
            # 既にalphaを持つ場合は一旦落としてからmaskを当てる
            base = fitz.Pixmap(base, 0)
        mask = fitz.Pixmap(doc.extract_image(smask)["image"])
        try:
            pix = fitz.Pixmap(base, mask)
        except Exception as e:
            # 合成に失敗した場合は本体画像のみで継続(黒背景の可能性は残る)
            logger.warning("Failed to merge smask (xref=%s): %s", xref, e)
            pix = fitz.Pixmap(doc.extract_image(xref)["image"])
        return pix.tobytes("png")

    # smaskなし: CMYK等の色空間もRGBのPNGへ正規化する
    pix = fitz.Pixmap(doc, xref)
    if pix.colorspace and pix.colorspace.n > 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    return pix.tobytes("png")


@app.post("/thumbnail/{paper_uuid}")
def create_thumbnail(paper_uuid: UUID):
    # ファイルの取得
    try:
        file_url = f"http://{PAPER_SVC_HOST}/paper/{paper_uuid}/download"
        logger.info("Fetch url: %s", file_url)
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
                # smaskを合成しPNGへ統一して取り出す (issue #353)
                filename = f"{p}-{j}.png"
                write_file_buffer[filename] = _extract_image_as_png(doc, img)

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
            content_type="image/png",
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
            404 if e.code in (
                "NoSuchKey",
                "NoSuchBucket",
                "ResourceNotFound") else 503)
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
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
