import asyncio
import collections
import os
import re
import sys
from typing import List, Literal, Optional, Dict
from uuid import UUID


import aiohttp
from fastapi import FastAPI, HTTPException
import MeCab
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

""" MongoDB Setup """
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "keyword")
MONGO_HOST = os.getenv("MONGO_HOST", "keyword-mongo")
MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/"

mongo_client = MongoClient(MONGO_CONNECTION_STRING)
db = mongo_client[MONGO_DBNAME]

SVC_PAPER_HOST = os.getenv("SERVICE_PAPER_HOST", "paper-app")
SVC_PAPER_PORT = os.getenv("SERVICE_PAPER_PORT", "8000")
SVC_FULLTEXT_HOST = os.getenv("SERVICE_FULLTEXT_HOST", "fulltext-app")
SVC_FULLTEXT_PORT = os.getenv("SERVICE_FULLTEXT_PORT", "8000")
REQ_TIMEOUT_SEC = int(os.getenv("REQUEST_TIMEOUT_SEC", 5))

TIMEOUT = aiohttp.ClientTimeout(total=REQ_TIMEOUT_SEC)


""" FastAPI Setup """
app = FastAPI()

""" Mecab """
wakati = MeCab.Tagger()


class ServiceHello(BaseModel):
    name: str


class ServiceHealth(BaseModel):
    resouce: str


class StatusResponse(BaseModel):
    status: Literal["ok", "error"]
    message: Optional[str] = ""


class KeywordCreateUpdate(BaseModel):
    paper_uuid: List[UUID]


class KeywordRead(BaseModel):
    paper_uuid: UUID
    keyword_counts: Dict[str, int]


class KeywordReadSeveral(BaseModel):
    keywords: List[KeywordRead]


# ファイル取得
async def http_get(
    session: aiohttp.ClientSession, url: str
):
    try:
        async with session.get(url) as response:
            if response.status != 200:
                response.raise_for_status()
            return await response.json()
    except Exception as e:
        print(e)
        raise e


@app.get("/", response_model=ServiceHello)
def root_handler():
    return ServiceHello(name="keyword")


@app.get("/healthz", response_model=StatusResponse)
def healthz_handler():
    return StatusResponse(status="ok", message="it works")


@app.get("/topz", response_model=ServiceHealth)
def topz_handler():
    return ServiceHealth(resource="busy")


@app.get("/keyword/{paper_uuid}", response_model=KeywordRead)
def read_keyword_handler(paper_uuid: UUID):
    query = {
        "paper_uuid": paper_uuid.hex
    }
    found_keywords = db["keyword"].find_one(query, {"_id": 0})
    return KeywordRead(**found_keywords)


@app.post("/keyword/{paper_uuid}", response_model=KeywordRead)
async def read_paper_handler(paper_uuid: UUID):
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        # タスク一覧
        tasks = []

        # fulltextサービスを呼び出し
        url = f"http://{SVC_FULLTEXT_HOST}:{SVC_FULLTEXT_PORT}/fulltext/{paper_uuid}"
        task = asyncio.create_task(
            http_get(session=session, url=url)
        )
        tasks.append(task)

        # 実行結果の集約
        try:
            json_raw = await asyncio.gather(*tasks)
        except Exception as e:
            print("Paper Download Error 2:", e)
            raise HTTPException(status_code=503)

    def _replace(text: str) -> str:
        x = text["text"].replace("テクニカルレポートCDSL Technical Report", "").replace(
            "c⃝ 2021 Cloud and Distributed Systems Laboratory", "")
        return x

    res_fulltext = json_raw[0]["fulltexts"]
    content = " ".join((map(_replace, res_fulltext)))

    # 形態素解析
    result = wakati.parse(content).splitlines()
    noun_words = list()
    for res in result:
        try:
            the_word = res.split("\t")[0]
            category = res.split("\t")[4]
            if "名詞" in category and not re.fullmatch('[0-9]+', the_word):
                noun_words.append(the_word)
        except Exception:
            continue

    uniq_word_counts = collections.Counter(noun_words)
    uniq_word_counts_filtered = list(
        filter(lambda x: x[1] >= 3, uniq_word_counts.items()))
    my_keyword = {
        "paper_uuid": paper_uuid.hex,
        "keyword_counts": uniq_word_counts_filtered
    }
    insert_id = db["keyword"].insert_one(my_keyword).inserted_id
    print("insert_id:", insert_id)
    return KeywordRead(**my_keyword)


# @app.get("/keyword/{paper_uuid}", response_model=KeywordRead)
# def read_paper_handler(paper_uuid: UUID):
#     entry = db["keyword"].find_one(
#         {"uuid": paper_uuid, "is_public": True}, {"_id": 0})
#     if entry:
#         return entry
#     else:
#         raise HTTPException(status_code=404, detail="Not Found")


# @app.delete("/reset", response_model=StatusResponse)
# def delete_paper_handler():
#     res = db["paper"].delete_many({})
#     print(res.deleted_count, " documents deleted.")
#     return StatusResponse(**{"status": "ok"})


if __name__ == "__main__":
    try:
        mongo_client.admin.command("ping")
        print("MongoDB connected.")
    except (ConnectionFailure, OperationFailure) as e:
        print("MongoDB not available. ", e)
        sys.exit(-1)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0")
