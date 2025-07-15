import os
import socket
import time
from curses import raw
from turtle import st
from typing import List, Literal, Optional
from uuid import UUID

import fitz
import requests
from elasticsearch import Elasticsearch
from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.elasticsearch import \
    ElasticsearchInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel

""" Paper Service """
PAPER_SVC_HOST = os.getenv("PAPER_SVC_HOST", "paper-app:8000")

""" Elasticsearch Setup """
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "fulltext-elastic:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "fulltext")

# OpenTelemetry TracerProvider の設定
resource = Resource(attributes={"service.name": "fulltext"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# OTLP Exporter の設定
otlp_exporter = OTLPSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Elasticsearch と Requests の計装
ElasticsearchInstrumentor().instrument()
RequestsInstrumentor().instrument()

for _ in range(120):
    try:
        _host = ELASTICSEARCH_HOST.split(":")[0]
        res = socket.getaddrinfo(_host, None)
        break
    except Exception as e:
        print("Retry resolve host:", e)
        time.sleep(1)

es = Elasticsearch(f"http://{ELASTICSEARCH_HOST}")

for i in range(300):
    print("try to connect elasticsearch", i)
    if es.ping():
        break
    time.sleep(1)


es.indices.create(index=ELASTICSEARCH_INDEX, ignore=400)


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


class FulltextRead(BaseModel):
    paper_uuid: UUID
    page_number: int
    text: str
    highlight: Optional[str] = None


class FulltextReadSeveral(BaseModel):
    fulltexts: List[FulltextRead]


@app.get("/", response_model=ServiceHello)
def root_handler():
    return {"name": "fulltext"}


@app.get("/healthz", response_model=StatusResponse)
def healthz_handler(response: Response):
    if es.ping():
        return StatusResponse(status="ok", message="it works")
    else:
        response.status_code = 503
        return StatusResponse(
            status="error",
            message="waiting for elasticsearch")


@app.get("/topz", response_model=ServiceHealth)
def topz_handler():
    return ServiceHealth(resource="busy")


@app.post("/fulltext/{paper_uuid}", response_model=StatusResponse)
def create_fulltext_handler(paper_uuid: UUID):
    # ファイルの取得
    try:
        file_url = f"http://{PAPER_SVC_HOST}/paper/{paper_uuid}/download"
        print("Fetch url:", file_url)
        pdf_data = requests.get(file_url)
    except Exception as e:
        print("Fail to download:", e)
        raise HTTPException(status_code=400,
                            detail="Cloud not downloads the file.")

    # PDFからテキストを取り出し
    with fitz.open(stream=pdf_data.content, filetype="pdf") as doc:
        for i in range(doc.page_count):
            raw_text = doc.get_page_text(pno=i)
            formated_text = raw_text.replace("\n", "")
            record = {
                "paper_uuid": paper_uuid,
                "page_number": i,
                "text": formated_text}
            print("Insert record:", record)
            try:
                es.index(index=ELASTICSEARCH_INDEX, document=record)
                # print(res)
            except Exception as e:
                print("Fail to create record:", e)
    return StatusResponse(status="ok", message="Created fulltext ")


@app.get("/fulltext/{paper_uuid}", response_model=FulltextReadSeveral)
def read_fulltext_handler(paper_uuid: UUID, background_tasks: BackgroundTasks):
    payload = {
        "query": {
            "match": {
                "paper_uuid": {
                    "query": paper_uuid,
                }
            }
        }
    }
    print("Elasticsearch Query:", payload)
    res = es.search(index=ELASTICSEARCH_INDEX, body=payload)
    records_count = int(res["hits"]["total"]["value"])
    if records_count == 0:
        print("Matched 0 records:")
        background_tasks.add_task(create_fulltext_handler, paper_uuid)
    records_list = list(
        map(lambda x: FulltextRead(**x["_source"]), res["hits"]["hits"])
    )
    return FulltextReadSeveral(fulltexts=records_list)


@app.get("/fulltext", response_model=FulltextReadSeveral)
def reads_fulltext_handler(keyword: str = ""):
    payload = {
        "query": {"match": {"text": {"query": keyword, "operator": "and"}}},
        "highlight": {"fields": {"text": {}}},
    }
    print("Elasticsearch Query:", payload)
    res = es.search(index=ELASTICSEARCH_INDEX, body=payload)
    records_list = []
    for hit in res["hits"]["hits"]:
        source = hit["_source"]
        highlight = hit.get("highlight", {}).get("text", [""])[0]
        records_list.append(FulltextRead(**source, highlight=highlight))
    return FulltextReadSeveral(fulltexts=records_list)


@app.delete("/reset", response_model=StatusResponse)
def delete_paper_handler():
    es.indices.delete(index=ELASTICSEARCH_INDEX, ignore=[400, 404])
    return StatusResponse(**{"status": "ok"})


if __name__ == "__main__":
    while True:
        try:
            _host = ELASTICSEARCH_HOST.split(":")[0]
            res = socket.getaddrinfo(_host, None)
            break
        except Exception as e:
            print("Retry resolve host:", e)
            time.sleep(1)

    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
