import logging
import os
import sys
from datetime import datetime
from http.client import HTTPException
from ipaddress import IPv4Address
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import \
    OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
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
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "stats")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/?uuidRepresentation=pythonLegacy"

# =============================================================================
# OpenTelemetry setup
# =============================================================================

resource = Resource(attributes={"service.name": "stats"})

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


class StatsCreateUpdate(BaseModel):
    paper_uuid: UUID
    ip_v4_addr: IPv4Address
    timestamp: datetime


class StatsCount(BaseModel):
    paper_uuid: UUID
    total_downloads: int


class StatsCountSeveral(BaseModel):
    stats: List[StatsCount]


@app.get("/", response_model=ServiceHello)
def root_handler():
    return ServiceHello(name="stats")


@app.get("/healthz", response_model=StatusResponse)
def healthz_handler():
    return StatusResponse(status="ok", message="it works")


@app.get("/topz", response_model=ServiceHealth)
def topz_handler():
    return ServiceHealth(resource="busy")


@app.get("/stats", response_model=StatsCountSeveral)
def read_stats_handler():
    query = [
        {
            "$group": {"_id": "$paper_uuid", "total_downloads": {"$sum": 1}},
        },
        {"$sort": {"total_downloads": -1}},
    ]
    logger.info("All Stats Query: %s", query)
    try:
        downloads = db["stats"].aggregate(query)
        res = []
        for x in list(downloads):
            sc = StatsCount(
                paper_uuid=x["_id"],
                total_downloads=x["total_downloads"])
            res.append(sc)
        return StatsCountSeveral(stats=res)
    except Exception:
        raise HTTPException(status_code=500, detail="Fail to select")


@app.post("/stats", response_model=StatusResponse)
def create_stats_handler(stats: StatsCreateUpdate):
    json_stats = jsonable_encoder(stats)
    my_stats = {
        "paper_uuid": json_stats.get("paper_uuid"),
        "ip_v4_addr": str(json_stats.get("ip_v4_addr")),
        "timestamp": datetime.now(),
    }
    try:
        insert_id = db["stats"].insert_one(my_stats).inserted_id
        logger.info("insert_id: %s", insert_id)
        return StatusResponse(status="ok",
                              message=f"Success insert = {insert_id}")
    except Exception:
        raise HTTPException(status_code=500, detail="Fail to insert")


@app.get("/stats/{paper_id}", response_model=StatsCount)
def read_stat_handler(paper_id: UUID):
    query = {"paper_uuid": str(paper_id)}
    logger.info("Stats Query: %s", query)
    try:
        downloads = db["stats"].count_documents(query)
        return StatsCount(paper_uuid=paper_id, total_downloads=downloads)
    except Exception:
        raise HTTPException(status_code=500, detail="Fail to select")


if __name__ == "__main__":
    try:
        client.admin.command("ping")
        logger.info("MongoDB connected.")
    except (ConnectionFailure, OperationFailure) as e:
        logger.error("MongoDB not available. %s", e)
        sys.exit(-1)

    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
