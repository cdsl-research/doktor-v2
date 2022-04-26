from curses import raw
import os
import socket
import time
from typing import List
from uuid import UUID

from elasticsearch import Elasticsearch
import fitz
import requests
from fastapi import FastAPI, HTTPException

""" Paper Service """
PAPER_SVC_HOST = os.getenv("PAPER_SVC_HOST", "paper-app:8000")

""" Elasticsearch Setup """
ELASTICSEARCH_HOST = os.getenv(
    "ELASTICSEARCH_HOST", "fulltext-elastic:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "fulltext")

es = Elasticsearch(f"http://{ELASTICSEARCH_HOST}")
es.indices.create(index=ELASTICSEARCH_INDEX, ignore=400)


""" FastAPI Setup """
app = FastAPI()


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
def create_fulltext_handler(paper_uuid: UUID):
    # ファイルの取得
    try:
        file_url = f"http://{PAPER_SVC_HOST}/paper/{paper_uuid}/download"
        print("Fetch url:", file_url)
        pdf_data = requests.get(file_url)
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Cloud not downloads the file.")

    # PDFからテキストを取り出し
    with fitz.open(stream=pdf_data.content, filetype="pdf") as doc:
        for i in range(doc.page_count):
            raw_text = doc.get_page_text(pno=i)
            formated_text = raw_text.replace("\n", "")
            record = {
                'paper_uuid': paper_uuid,
                'page_number': i,
                'text': formated_text
            }
            try:
                res = es.index(index=ELASTICSEARCH_INDEX, document=record)
                print(res)
            except Exception as e:
                print(e)
    return {"status": "ok"}


@app.get("/fulltext/{paper_uuid}")
def read_fulltext_handler(paper_uuid: UUID):
    payload = {
        "query": {
            "match": {
                "paper_uuid": {
                    "query": paper_uuid,
                }
            }
        }
    }
    res = es.search(index=ELASTICSEARCH_INDEX, body=payload)
    # records_count = res["hits"]["total"]["value"]
    records_list = list(map(lambda x: x["_source"], res["hits"]["hits"]))
    # print(records_list)
    return records_list


@app.get("/fulltext")
def reads_fulltext_handler(keyword: str = ""):
    payload = {
        "query": {
            "match": {
                "text": {
                    "query": keyword,
                    "operator": "and"
                }
            }
        }
    }
    res = es.search(index=ELASTICSEARCH_INDEX, body=payload)
    records_list = list(map(lambda x: x["_source"], res["hits"]["hits"]))
    return records_list


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
