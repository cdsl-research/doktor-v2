import asyncio
import io
import os
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, Request, HTTPException, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
import aiohttp

SVC_PAPER_HOST = os.getenv("SERVICE_PAPER_HOST", "paper-app")
SVC_PAPER_PORT = os.getenv("SERVICE_PAPER_PORT", "8000")
SVC_AUTHOR_HOST = os.getenv("SERVICE_AUTHOR_HOST", "author-app")
SVC_AUTHOR_PORT = os.getenv("SERVICE_AUTHOR_PORT", "8000")

app = FastAPI()
templates = Jinja2Templates(directory="templates")


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


@app.get("/")
async def top_handler(request: Request):
    return templates.TemplateResponse("top.html", {"request": request})


@app.get("/paper")
async def read_paper_list_handler(request: Request):
    url = f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper"
    async with aiohttp.ClientSession() as session:
        try:
            res_paper = await fetch(session, url)
        except BaseException:
            raise HTTPException(status_code=503, detail="Internal Error")

    paper_details = []
    for rp in res_paper['papers']:
        paper_details.append({
            "uuid": rp.get("uuid", "#"),
            "title": rp.get("title", "No Title"),
            "label": rp.get("label", "No Label"),
            "created_at": rp.get("created_at")
        })

    return templates.TemplateResponse("paper.html", {
        "request": request,
        "papers": paper_details
    })


@app.get("/paper/add")
async def add_paper_exec_handler(request: Request):
    url = f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author"
    async with aiohttp.ClientSession() as session:
        try:
            res_author = await fetch(session, url)
        except BaseException:
            raise HTTPException(status_code=503, detail="Internal Error")

    author_details = [{
        "uuid": author.get("uuid", ""),
        "name": author.get("last_name_ja") + author.get("first_name_ja")
    } for author in res_author]
    return templates.TemplateResponse("paper-add.html", {
        "request": request,
        "authors": author_details
    })


@app.post("/paper/add")
async def add_paper_handler(request: Request,
                            title: str = Form(...),
                            author1: str = Form(...),
                            author2: Optional[str] = Form(None),
                            author3: Optional[str] = Form(None),
                            keywords: Optional[List[str]] = Form([]),
                            label: Optional[str] = Form(""),
                            publish: bool = Form(True),
                            pdffile: UploadFile = File(...)
                            ):
    author_list = [author1]
    if author2:
        author_list.append(author2)
    if author3:
        author_list.append(author3)
    req_body = {
        "author_uuid": author_list,
        "title": title,
        "keywords": keywords,
        "label": label,
        "categories_id": [
            0
        ],
        "abstract": "ここにabstractが入る．",
        "url": "https://ja.tak-cslab.org/",
        "thumbnail_url": "https://ja.tak-cslab.org/",
        "is_public": publish
    }
    print("Request1:", req_body)

    async with aiohttp.ClientSession() as session:
        try:
            """ Add paper info """
            url_meta = f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper"
            print("Req1 url:", url_meta)
            async with session.post(url_meta, json=req_body) as res_meta:
                if res_meta.status != 200:
                    print("Invalid status1:", res_meta.status)
                    print("Response1:", res_meta.json)
                    raise HTTPException(status_code=503,
                                        detail="Internal Error")
                res_meta_detail = await res_meta.json()
                if res_meta_detail.get("uuid"):
                    paper_uuid = res_meta_detail.get("uuid")
                else:
                    raise HTTPException(status_code=503,
                                        detail="Internal Error")

            """ Add paper pdf file """
            url_file = (f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}"
                        f"/paper/{paper_uuid}/upload")
            file_content = pdffile.file.read()
            payload = aiohttp.FormData()
            payload.add_field('file', io.BytesIO(file_content),
                              filename=f"{paper_uuid}.pdf",
                              content_type='application/pdf')
            print("Req2 url:", url_file)
            async with session.post(url_file, data=payload) as res_body:
                if res_body.status != 200:
                    print("Invalid status2:", res_body.status)
                    print("Response2:", res_body.json)
                    raise HTTPException(status_code=503,
                                        detail="Internal Error")
                res_body_detail = res_body.json()
                print("req2 response:", res_body_detail)

        except Exception as e:
            print("HTTP Request failed:", e)
            raise HTTPException(status_code=503, detail="Internal Error")

    return {"status": "ok"}
    # return templates.TemplateResponse("paper-add.html", {"request": request})


@app.get("/paper/{paper_uuid}/edit")
async def update_paper_handler(paper_uuid: UUID, request: Request):
    urls = (f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author",
            f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper/{paper_uuid}")
    async with aiohttp.ClientSession() as session:
        try:
            res_json = await fetch_all(session, urls)
        except BaseException:
            raise HTTPException(status_code=503, detail="Internal Error")
    res_author = res_json[0]
    res_paper = res_json[1]

    found_author = []
    for author_uuid in res_paper.get("author_uuid"):
        candidates = filter(lambda x: author_uuid == x.get("uuid"), res_author)
        candidates_lst = list(candidates)
        if len(candidates_lst) > 0:
            author = candidates_lst[0]
            display_name = author.get('last_name_ja') + " " + \
                author.get('first_name_ja')
            found_author.append(
                {"label": display_name, "uuid": author.get("uuid")})

    if len(found_author) != 3:
        additional_item = 3 - len(found_author)
        for _ in range(additional_item):
            found_author.append("")

    return templates.TemplateResponse("paper-edit.html", {
        "request": request,
        "paper": res_paper,
        "authors": res_author,
        "default_authors": found_author
    })
    print(found_author)
    print(res_paper)


@ app.get("/author")
async def read_author_list_handler(request: Request):
    url = f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author"
    async with aiohttp.ClientSession() as session:
        try:
            res_author = await fetch(session, url)
        except BaseException:
            raise HTTPException(status_code=503, detail="Internal Error")

    author_details = []
    for rp in res_author:
        author_details.append({
            "first_name_ja": rp.get("first_name_ja"),
            "middle_name_ja": rp.get("middle_name_ja"),
            "last_name_ja": rp.get("last_name_ja"),
            "first_name_en": rp.get("first_name_en"),
            "middle_name_en": rp.get("middle_name_en"),
            "last_name_en": rp.get("last_name_en"),
            "joined_year": rp.get("joined_year"),
            "is_graduated": rp.get("is_graduated"),
            "created_at": rp.get("created_at"),
            "updated_at": rp.get("updated_at")
        })

    return templates.TemplateResponse("author.html", {
        "request": request,
        "authors": author_details
    })


@ app.get("/author/add")
def add_author_handler(request: Request):
    return templates.TemplateResponse("author-add.html", {"request": request})


@ app.post("/author/add")
async def add_author_exec_handler(request: Request,
                                  first_name_ja: str = Form(...),
                                  middle_name_ja: Optional[str] = Form(None),
                                  last_name_ja: str = Form(...),
                                  first_name_en: str = Form(...),
                                  middle_name_en: Optional[str] = Form(None),
                                  last_name_en: str = Form(...),
                                  joined_year: int = Form(...),
                                  graduation: bool = Form(...)
                                  ):
    url = f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author"
    req_body = {
        "first_name_ja": first_name_ja,
        "middle_name_ja": middle_name_ja if middle_name_ja else "",
        "last_name_ja": last_name_ja,
        "first_name_en": first_name_en,
        "middle_name_en": middle_name_en if middle_name_en else "",
        "last_name_en": last_name_en,
        "joined_year": joined_year,
        "is_graduated": graduation
    }
    print("Request Body:", req_body)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=req_body) as response:
                if response.status != 200:
                    print("Invalid status:", response.status)
                    print("Response:", response.json)
                    raise HTTPException(status_code=503,
                                        detail="Internal Error")
                res = await response.json()
        except Exception as e:
            print("HTTP Request failed:", e)
            raise HTTPException(status_code=503, detail="Internal Error")

    return templates.TemplateResponse("author-add-exec.html", {
        "request": request,
        "author": res
    })
