import asyncio
import os
from typing import List, Optional

from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import aiohttp

SVC_PAPER_HOST = os.getenv("SERVICE_PAPER_HOST", "paper-dind")
SVC_PAPER_PORT = os.getenv("SERVICE_PAPER_PORT", "4100")
SVC_AUTHOR_HOST = os.getenv("SERVICE_AUTHOR_HOST", "author-dind")
SVC_AUTHOR_PORT = os.getenv("SERVICE_AUTHOR_PORT", "4200")

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
    for rp in res_paper:
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
def add_paper_handler(request: Request,
                      title: str = Form(...),
                      author: List[str] = Form(...),
                      keywords: Optional[str] = Form(None),
                      label: Optional[str] = Form(None),
                      publish: bool = Form(True),
                      pdffile: bytes = File(...)
                      ):
    return {
        "title": title,
        "author": author,
        "keywords": keywords,
        "label": label,
        "publish": publish,
        "pdffile": len(pdffile)
    }
    # return templates.TemplateResponse("paper-add.html", {"request": request})


@app.get("/author")
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


@app.get("/author/add")
def add_author_handler(request: Request):
    return templates.TemplateResponse("author-add.html", {"request": request})


@app.post("/author/add")
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
