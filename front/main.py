import asyncio
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import aiohttp

app = FastAPI()
templates = Jinja2Templates(directory="templates")


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
    urls = ("http://localhost:4100/paper", "http://localhost:4200/author")
    async with aiohttp.ClientSession() as session:
        json_raw = await fetch_all(session, urls)
    res_paper = json_raw[0]
    res_author = json_raw[1]

    paper_details = []
    for rp in res_paper:
        found_author = list(filter(lambda x: x.get("uuid") in rp.get("author_uuid"), res_author))
        author_list = [{"name": fa.get("last_name_ja") + fa.get("first_name_ja"),
                        "uuid": fa.get("uuid")} for fa in found_author]
        paper_details.append({
            "uuid": rp.get("uuid", "#"),
            "title": rp.get("title", "No Title"),
            "author": author_list,
            "label": rp.get("label", "No Label"),
            "created_at": rp.get("created_at")
        })

    # sample_data = [{"title": "my title", "author": "my author", "label": "my label", "created_at": "2021/02/03"}]
    return templates.TemplateResponse("top.html", {"request": request, "papers": paper_details})


@app.get("/paper/{paper_uuid}", response_class=HTMLResponse)
async def paper_handler(paper_uuid: UUID, request: Request):
    urls = ("http://localhost:4200/author", f"http://localhost:4100/paper/{paper_uuid}")
    async with aiohttp.ClientSession() as session:
        json_raw = await fetch_all(session, urls)
    res_author = json_raw[0]
    res_paper_me = json_raw[1]

    found_author = list(filter(lambda x: x.get("uuid") in res_paper_me["author_uuid"], res_author))
    paper_details = {
        "title": res_paper_me.get("title"),
        "author": [{
            "name": author.get("last_name_ja") + author.get("first_name_ja"),
            "uuid": author.get("uuid")
        } for author in found_author],
        "keywords": res_paper_me.get("keywords"),
        "label": res_paper_me.get("label"),
        "created_at": res_paper_me.get("created_at"),
        "updated_at": res_paper_me.get("updated_at"),
        "abstract": res_paper_me.get("abstract")
    }

    return templates.TemplateResponse("paper.html", {"request": request, "paper": paper_details})


@app.get("/author/{author_uuid}", response_class=HTMLResponse)
async def author_handler(author_uuid: UUID, request: Request):
    urls = ("http://localhost:4100/paper", "http://localhost:4200/author",
            f"http://localhost:4200/author/{author_uuid}")
    async with aiohttp.ClientSession() as session:
        json_res = await fetch_all(session, urls)
    res_paper = json_res[0]
    res_author = json_res[1]
    res_author_me = json_res[2]

    # 著者(author_uuid)を含む論文一覧を取得
    found_paper = list(filter(lambda x: str(author_uuid) in x["author_uuid"], res_paper))
    paper_details = []
    for fp in found_paper:
        # 個々の論文の著者ID(uuid)を氏名に変換
        found_author = list(filter(lambda x: x["uuid"] in fp.get("author_uuid"), res_author))
        author_list = [{"name": fa.get("last_name_ja") + fa.get("first_name_ja"),
                        "uuid": fa.get("uuid")} for fa in found_author]
        paper_details.append({
            "title": fp.get("title", "No Title"),
            "author": author_list,
            "label": fp.get("label", "No Label"),
            "created_at": fp.get("created_at")
        })

    author_details = {
        "name": res_author_me.get("last_name_ja") + res_author_me.get("first_name_ja"),
        "status": "在学" if res_author_me.get("is_graduated") else "既卒",
        "joined_year": res_author_me.get("joined_year")
    }

    return templates.TemplateResponse("author.html",
                                      {"request": request, "papers": paper_details, "author": author_details})