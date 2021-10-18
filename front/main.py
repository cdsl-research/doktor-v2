import asyncio
import os
from datetime import datetime as dt
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
import aiohttp

SVC_PAPER_HOST = os.getenv("SERVICE_PAPER_HOST", "paper-dind")
SVC_PAPER_PORT = os.getenv("SERVICE_PAPER_PORT", "4100")
SVC_AUTHOR_HOST = os.getenv("SERVICE_AUTHOR_HOST", "author-dind")
SVC_AUTHOR_PORT = os.getenv("SERVICE_AUTHOR_PORT", "4200")

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# 日付のフォーマットを修正
def reformat_datetime(raw_str: str) -> str:
    _created = dt.strptime(raw_str, "%Y-%m-%dT%H:%M:%S.%f")
    return _created.strftime("%b. %d, %Y")


async def fetch_file(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()
        return await response.read()


async def fetch(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()
        return await response.json()


async def fetch_all(session, urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch(session, url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


@app.get("/", response_class=HTMLResponse)
async def top_handler(request: Request):
    urls = (f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper",
            f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author")
    async with aiohttp.ClientSession() as session:
        json_raw = await fetch_all(session, urls)
    res_paper = json_raw[0]
    res_author = json_raw[1]

    paper_details = []
    for rp in res_paper:  # 論文を選択
        # 論文に対応する著者名を検索
        found_author = []
        for uuid in rp.get("author_uuid"):
            candidates = filter(lambda x: uuid == x.get("uuid"), res_author)
            candidates_lst = list(candidates)
            if len(candidates_lst) > 0:
                author = candidates_lst[0]
                display_name = author.get('last_name_ja') + " " + \
                               author.get('first_name_ja')
                found_author.append(display_name)

        paper_details.append({
            "uuid": rp.get("uuid", "#"),
            "title": rp.get("title", "No Title"),
            "author": found_author,
            "label": rp.get("label", "No Label"),
            "created_at": reformat_datetime(rp.get("created_at"))
        })

    return templates.TemplateResponse("top.html", {
        "request": request,
        "papers": paper_details
    })


@app.get("/paper/{paper_uuid}", response_class=HTMLResponse)
async def paper_handler(paper_uuid: UUID, request: Request):
    urls = (f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author",
            f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper/{paper_uuid}")
    async with aiohttp.ClientSession() as session:
        json_raw = await fetch_all(session, urls)
    res_author = json_raw[0]
    res_paper_me = json_raw[1]

    found_author = []
    for uuid in res_paper_me["author_uuid"]:
        candidates = filter(lambda x: uuid == x.get("uuid"), res_author)
        candidates_lst = list(candidates)
        if len(candidates_lst) > 0:
            author = candidates_lst[0]
            found_author.append(author)

    paper_details = {
        "uuid": res_paper_me.get("uuid"),
        "title": res_paper_me.get("title"),
        "author": [{
            "name": author.get("last_name_ja") + author.get("first_name_ja"),
            "uuid": author.get("uuid")
        } for author in found_author],
        "keywords": res_paper_me.get("keywords"),
        "label": res_paper_me.get("label"),
        "created_at": reformat_datetime(res_paper_me.get("created_at")),
        "updated_at": reformat_datetime(res_paper_me.get("updated_at")),
        "abstract": res_paper_me.get("abstract")
    }

    return templates.TemplateResponse(
        "paper.html", {
            "request": request,
            "paper": paper_details,
            "page_title": f"{paper_details['title']}"
        })


@app.get("/paper/{paper_uuid}/download", response_class=HTMLResponse)
async def paper_download_handler(paper_uuid: UUID, request: Request):
    async with aiohttp.ClientSession() as session:
        url = f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper/{paper_uuid}/download"
        res_pdf = await fetch_file(session, url)
    return Response(content=res_pdf, media_type="application/pdf")


@app.get("/author/{author_uuid}", response_class=HTMLResponse)
async def author_handler(author_uuid: UUID, request: Request):
    urls = (f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper",
            f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author",
            f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author/{author_uuid}")
    async with aiohttp.ClientSession() as session:
        json_res = await fetch_all(session, urls)
    res_paper = json_res[0]
    res_author = json_res[1]
    res_author_me = json_res[2]

    # 著者(author_uuid)を含む論文一覧を取得
    found_paper = list(filter(
        lambda x: str(author_uuid) in x["author_uuid"],
        res_paper))
    paper_details = []
    for fp in found_paper:
        # 個々の論文の著者ID(uuid)を氏名に変換
        found_author = []
        for uuid in fp.get("author_uuid"):
            candidates = filter(lambda x: uuid == x.get("uuid"), res_author)
            candidates_lst = list(candidates)
            if len(candidates_lst) > 0:
                author = candidates_lst[0]
                display_name = author.get('last_name_ja') + " " + \
                               author.get('first_name_ja')
                found_author.append(display_name)

        paper_details.append({
            "uuid": fp.get("uuid", "#"),
            "title": fp.get("title", "No Title"),
            "author": found_author,
            "label": fp.get("label", "No Label"),
            "created_at": reformat_datetime(fp.get("created_at"))
        })

    author_details = {
        "name": res_author_me.get("last_name_ja") +
        res_author_me.get("first_name_ja"),
        "status": "既卒" if res_author_me.get("is_graduated") else "在学",
        "joined_year": res_author_me.get("joined_year")
    }

    return templates.TemplateResponse("author.html", {
        "request": request,
        "papers": paper_details,
        "author": author_details,
        "page_title": author_details["name"]
    })
