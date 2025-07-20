import logging
import os
import sys
from datetime import datetime
from email import message
from typing import List, Literal, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "author")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/?uuidRepresentation=pythonLegacy"

# OpenTelemetry TracerProvider の設定
resource = Resource(attributes={"service.name": "author"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# OTLP Exporter の設定
otlp_exporter = OTLPSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# PyMongo の計装
PymongoInstrumentor().instrument()

client = MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DBNAME]

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


class AuthorReadSeveral(BaseModel):
    authors: List[AuthorRead]


@app.get("/", response_model=ServiceHello)
def root_handler():
    return ServiceHello(name="author")


@app.get("/healthz", response_model=StatusResponse)
def healthz_handler():
    return StatusResponse(status="ok", message="it works")


@app.get("/topz", response_model=ServiceHealth)
def topz_handler():
    return ServiceHealth(resource="busy")


@app.post("/author", response_model=AuthorRead)
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
        "updated_at": datetime.now(),
    }
    insert_id = db["author"].insert_one(my_author).inserted_id
    logger.info("insert_id: %s", insert_id)
    return AuthorRead(**my_author)


@app.get("/author")
def read_authors_handler(name: str = ""):
    target_fields = [
        "first_name_ja",
        "middle_name_ja",
        "last_name_ja",
        "first_name_en",
        "middle_name_en",
        "last_name_en",
    ]
    or_conditions = [{tf: {"$regex": name}} for tf in target_fields]
    query = {"$or": or_conditions}
    logger.info("Mongo Query: %s", query)
    return list(db["author"].find(query, {"_id": 0}))


# @app.get("/author", response_model=AuthorReadSeveral)
# def read_authors_handler():
#     authors = list(db["author"].find({}, {'_id': 0}))
#     return AuthorReadSeveral(authors=authors)


@app.get("/author/{author_uuid}", response_model=AuthorRead)
def read_author_handler(author_uuid: UUID):
    entry = db["author"].find_one({"uuid": author_uuid}, {"_id": 0})
    if entry:
        return AuthorRead(**entry)
    else:
        raise HTTPException(status_code=404, detail="Not Found")


# @app.put("/author/{author_uuid}", response_model=AuthorRead)
# def update_author_handler(author_uuid: UUID, author: AuthorCreateUpdate):
#     json_author = jsonable_encoder(author)
#     my_author = {
#         "uuid": author_uuid,
#         "first_name_ja": json_author.get("first_name_ja"),
#         "middle_name_ja": json_author.get("middle_name_ja"),
#         "last_name_ja": json_author.get("last_name_ja"),
#         "first_name_en": json_author.get("first_name_en"),
#         "middle_name_en": json_author.get("middle_name_en"),
#         "last_name_en": json_author.get("last_name_en"),
#         "joined_year": json_author.get("joined_year"),
#         "is_graduated": json_author.get("is_graduated"),
#         "created_at": datetime.now(),  # todo: get stored data
#         "updated_at": datetime.now()
#     }
#     return AuthorRead(**my_author)


@app.delete("/reset", response_model=StatusResponse)
def delete_author_handler():
    res = db["author"].delete_many({})
    logger.info("%d documents deleted.", res.deleted_count)
    return StatusResponse(**{"status": "ok"})


if __name__ == "__main__":
    try:
        client.admin.command("ping")
        logger.info("MongoDB connected.")
    except (ConnectionFailure, OperationFailure) as e:
        logger.error("MongoDB not available. %s", e)
        sys.exit(-1)

    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
