import logging
import os
import re
import socket
import sys
import time
from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID, uuid4

import urllib3
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from minio import Minio, S3Error
from minio.deleteobjects import DeleteObject
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import \
    OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "paper")
MONGO_HOST = os.getenv("MONGO_HOST", "paper-mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/?uuidRepresentation=pythonLegacy"
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minio")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minio123")
MINIO_HOST = os.getenv("MINIO_HOST", "paper-minio:9000")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "paper")

# =============================================================================
# OpenTelemetry setup
# =============================================================================

resource = Resource(attributes={"service.name": "paper"})

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

# PyMongo と Requests の計装
PymongoInstrumentor().instrument()
RequestsInstrumentor().instrument()

mongo_client = MongoClient(MONGO_CONNECTION_STRING)
db = mongo_client[MONGO_DBNAME]

try:
    minio_client = Minio(
        MINIO_HOST,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
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


class PaperCreateUpdate(BaseModel):
    author_uuid: List[UUID]
    title: str
    label: str
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime] = datetime.now()


class PaperRead(BaseModel):
    uuid: UUID
    author_uuid: List[UUID]
    title: str
    label: str
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime] = datetime.now()
    # todo) reference_id: List[int]


class PaperReadSeveral(BaseModel):
    papers: List[PaperRead]


@app.get("/", response_model=ServiceHello)
def root_handler():
    return ServiceHello(name="paper")


@app.get("/healthz", response_model=StatusResponse)
def healthz_handler():
    return StatusResponse(status="ok", message="it works")


@app.get("/topz", response_model=ServiceHealth)
def topz_handler():
    return ServiceHealth(resource="busy")


@app.post("/paper", response_model=PaperRead)
def create_paper_handler(paper: PaperCreateUpdate):
    json_paper = jsonable_encoder(paper)
    my_paper = {
        "uuid": uuid4(),
        "author_uuid": json_paper.get("author_uuid"),
        "title": json_paper.get("title"),
        "label": json_paper.get("label"),
        "is_public": json_paper.get("is_public"),
        "created_at": json_paper.get("created_at"),
        "updated_at": json_paper.get("updated_at"),
    }
    insert_id = db["paper"].insert_one(my_paper).inserted_id
    logger.info("insert_id: %s", insert_id)
    return PaperRead(**my_paper)


@app.get("/paper", response_model=PaperReadSeveral)
def read_papers_handler(private: bool = False, title: str = ""):
    query = {"is_public": True}
    if private:
        del query["is_public"]

    if title:
        _title = title.strip()
        validate = re.search("^[0-9a-zA-Zあ-んア-ン一-鿐ー]+$", _title)
        if validate is None:
            raise HTTPException(status_code=400, detail="Invalid input")
        else:
            query["title"] = {"$regex": title}

    found_papers = db["paper"].find(query, {"_id": 0}).sort("label", -1)
    read_papers = list(map(lambda x: PaperRead(**x), found_papers))
    return PaperReadSeveral(papers=read_papers)


@app.get("/paper/{paper_uuid}", response_model=PaperRead)
def read_paper_handler(paper_uuid: UUID):
    entry = db["paper"].find_one(
        {"uuid": paper_uuid, "is_public": True}, {"_id": 0})
    if entry:
        return entry
    else:
        raise HTTPException(status_code=404, detail="Not Found")


@app.post("/paper/{paper_uuid}/upload", response_model=StatusResponse)
async def upload_paper_file_handler(
        paper_uuid: UUID,
        file: UploadFile = File(...)):
    try:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Invalid Content-Type")
        # print("file number:", file.file.fileno())
        exist = minio_client.bucket_exists(MINIO_BUCKET_NAME)
        if not exist:
            minio_client.make_bucket(MINIO_BUCKET_NAME)
        response = minio_client.put_object(
            MINIO_BUCKET_NAME,
            f"{paper_uuid}.pdf",
            file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type="application/pdf",
        )
        return StatusResponse(**{"status": "ok"})
        response.close()
        response.release_conn()
    except S3Error as e:
        logger.error("Upload exception: %s", e)
        raise HTTPException(status_code=503, detail=str(e.message))


@app.get(
    "/paper/{paper_uuid}/download",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Return the PDF file",
        }
    },
)
async def download_paper_handler(paper_uuid: UUID):
    try:
        response = minio_client.get_object(
            MINIO_BUCKET_NAME, f"{paper_uuid}.pdf")
        return Response(content=response.read(), media_type="application/pdf")
        response.close()
        response.release_conn()
    except S3Error as e:
        logger.error("Download exception: %s", e)
        _status_code = (
            404 if e.code in (
                "NoSuchKey",
                "NoSuchBucket",
                "ResourceNotFound") else 503)
        raise HTTPException(status_code=_status_code, detail=str(e.message))


# @app.put("/paper/{paper_uuid}", response_model=PaperRead)
# def update_paper_handler(paper_uuid: UUID, paper: PaperCreateUpdate):
#     json_paper = jsonable_encoder(paper)
#     my_paper = {
#         "uuid": paper_uuid,
#         "author_uuid": json_paper.get("author_uuid"),
#         "title": json_paper.get("title"),
#         "label": json_paper.get("label"),
#         "is_public": json_paper.get("is_public"),
#         "created_at": json_paper.get("created_at"),
#         "updated_at": json_paper.get("updated_at"),
#     }
#     return PaperRead(**my_paper)


@app.delete("/reset", response_model=StatusResponse)
def delete_paper_handler():
    res = db["paper"].delete_many({})
    logger.info("%d documents deleted.", res.deleted_count)
    delete_object_list = map(
        lambda x: DeleteObject(x.object_name),
        minio_client.list_objects(MINIO_BUCKET_NAME, recursive=True),
    )
    errors = minio_client.remove_objects(MINIO_BUCKET_NAME, delete_object_list)
    for error in errors:
        logger.error("error occured when deleting object %s", error)
    return StatusResponse(**{"status": "ok"})


if __name__ == "__main__":
    try:
        mongo_client.admin.command("ping")
        logger.info("MongoDB connected.")
    except (ConnectionFailure, OperationFailure) as e:
        logger.error("MongoDB not available. %s", e)
        sys.exit(-1)

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
