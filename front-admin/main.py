import asyncio
import io
import os
from asyncio.base_subprocess import ReadSubprocessPipeProto
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import aiohttp
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates

SVC_PAPER_HOST = os.getenv("SERVICE_PAPER_HOST", "paper-app")
SVC_PAPER_PORT = os.getenv("SERVICE_PAPER_PORT", "8000")
SVC_AUTHOR_HOST = os.getenv("SERVICE_AUTHOR_HOST", "author-app")
SVC_AUTHOR_PORT = os.getenv("SERVICE_AUTHOR_PORT", "8000")
SVC_THUMBNAIL_HOST = os.getenv("SERVICE_THUMBNAIL_HOST", "thumbnail-app")
SVC_THUMBNAIL_PORT = os.getenv("SERVICE_THUMBNAIL_PORT", "8000")
SVC_FULLTEXT_HOST = os.getenv("SERVICE_FULLTEXT_HOST", "fulltext-app")
SVC_FULLTEXT_PORT = os.getenv("SERVICE_FULLTEXT_PORT", "8000")

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
    for rp in res_paper["papers"]:
        paper_details.append(
            {
                "uuid": rp.get("uuid", "#"),
                "title": rp.get("title", "No Title"),
                "label": rp.get("label", "No Label"),
                "created_at": rp.get("created_at"),
            }
        )

    return templates.TemplateResponse(
        "paper.html", {"request": request, "papers": paper_details}
    )


@app.get("/paper/add")
async def add_paper_handler(request: Request):
    url = f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author"
    async with aiohttp.ClientSession() as session:
        try:
            res_author = await fetch(session, url)
        except BaseException:
            raise HTTPException(status_code=503, detail="Internal Error")

    author_details = [
        {
            "uuid": author.get("uuid", ""),
            "name": author.get("last_name_ja") + author.get("first_name_ja"),
        }
        for author in res_author
    ]
    return templates.TemplateResponse(
        "paper-add.html", {"request": request, "authors": author_details}
    )


@app.post("/paper/add", response_class=RedirectResponse, status_code=302)
async def add_paper_exec_handler(
    request: Request,
    title: str = Form(...),
    author1: str = Form(...),
    author2: Optional[str] = Form(None),
    author3: Optional[str] = Form(None),
    label: Optional[str] = Form(""),
    publish: bool = Form(True),
    pdffile: UploadFile = File(...),
):
    author_list = [author1]
    if author2:
        author_list.append(author2)
    if author3:
        author_list.append(author3)
    req_body = {
        "author_uuid": author_list,
        "title": title.stip(),
        "label": label.stip(),
        "is_public": publish,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_public": publish,
    }

    async with aiohttp.ClientSession() as session:
        try:
            """Add paper info"""
            url_meta = f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper"
            print("Request url for paper_meta:", url_meta)
            async with session.post(url_meta, json=req_body) as res_meta:
                if res_meta.status != 200:
                    print("Invalid status on meta:", res_meta.status)
                    print("Response on meta:", res_meta.json)
                    raise HTTPException(
                        status_code=503, detail="Internal Error")
                res_meta_detail = await res_meta.json()
                if res_meta_detail.get("uuid"):
                    paper_uuid = res_meta_detail.get("uuid")
                else:
                    raise HTTPException(
                        status_code=503, detail="Internal Error")
                print("Response on meta:", res_meta_detail)

            """ Add paper pdf file """
            url_file = (
                f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}"
                f"/paper/{paper_uuid}/upload"
            )
            file_content = pdffile.file.read()
            payload = aiohttp.FormData()
            payload.add_field(
                "file",
                io.BytesIO(file_content),
                filename=f"{paper_uuid}.pdf",
                content_type="application/pdf",
            )
            print("Request url for paper_file:", url_file)
            async with session.post(url_file, data=payload) as res_file:
                if res_file.status != 200:
                    print("Invalid status on file:", res_file.status)
                    print("Response on file:", res_file.json)
                    raise HTTPException(
                        status_code=503, detail="Internal Error")
                res_file_detail = res_file.json()
                print("Response on file:", res_file_detail)

        except Exception as e:
            print("HTTP Request failed:", e)
            raise HTTPException(status_code=503, detail="Internal Error")

    async with aiohttp.ClientSession() as session:
        try:
            """Add fulltext"""
            url_text = (
                f"http://{SVC_FULLTEXT_HOST}:{SVC_FULLTEXT_PORT}"
                f"/fulltext/{paper_uuid}"
            )
            print("Request url for text:", url_text)
            async with session.post(url_text) as res_text:
                if res_text.status != 200:
                    print("Invalid status on text:", res_text.status)
                    raise HTTPException(
                        status_code=503, detail="Internal Error")
                res_text_detail = res_text.json()
                print("Response on text:", res_text_detail)

            # """ Add thumbnail """
            # url_thumb = (f"http://{SVC_THUMBNAIL_HOST}:{SVC_THUMBNAIL_PORT}"
            #              f"/thumbnail/{paper_uuid}")
            # print("Request url for thumbnail:", url_thumb)
            # async with session.post(url_thumb) as res_thumb:
            #     if res_thumb.status != 200:
            #         print("Invalid status on text:", res_thumb.status)
            #         raise HTTPException(status_code=503,
            #                             detail="Internal Error")
            #     res_thumb = res_thumb.json()
            #     print("Response on thumbnail:", res_thumb)
        except Exception as e:
            print("HTTP Request failed:", e)
            raise HTTPException(status_code=503, detail="Internal Error")

    return "/paper"


@app.get("/paper/{paper_uuid}", response_class=Response)
async def paper_download_handler(paper_uuid: UUID, request: Request):
    async with aiohttp.ClientSession() as session:
        url = f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper/{paper_uuid}/download"
        try:
            res_pdf = await fetch_file(session, url)
        except aiohttp.ClientResponseError as e:
            print("Paper Download Error:", e)
            if e.code == 404:
                raise HTTPException(status_code=404)
            raise HTTPException(status_code=503)
    return Response(content=res_pdf, media_type="application/pdf")


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
        author_details.append(
            {
                "first_name_ja": rp.get("first_name_ja"),
                "middle_name_ja": rp.get("middle_name_ja"),
                "last_name_ja": rp.get("last_name_ja"),
                "first_name_en": rp.get("first_name_en"),
                "middle_name_en": rp.get("middle_name_en"),
                "last_name_en": rp.get("last_name_en"),
                "joined_year": rp.get("joined_year"),
                "is_graduated": rp.get("is_graduated"),
                "created_at": rp.get("created_at"),
                "updated_at": rp.get("updated_at"),
            }
        )

    return templates.TemplateResponse(
        "author.html", {"request": request, "authors": author_details}
    )


@app.get("/author/add")
def add_author_handler(request: Request):
    return templates.TemplateResponse("author-add.html", {"request": request})


@app.post("/author/add")
async def add_author_exec_handler(
    request: Request,
    first_name_ja: str = Form(...),
    middle_name_ja: Optional[str] = Form(None),
    last_name_ja: str = Form(...),
    first_name_en: str = Form(...),
    middle_name_en: Optional[str] = Form(None),
    last_name_en: str = Form(...),
    joined_year: int = Form(...),
    graduation: bool = Form(...),
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
        "is_graduated": graduation,
    }
    print("Request Body:", req_body)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=req_body) as response:
                if response.status != 200:
                    print("Invalid status:", response.status)
                    print("Response:", response.json)
                    raise HTTPException(
                        status_code=503, detail="Internal Error")
                res = await response.json()
        except Exception as e:
            print("HTTP Request failed:", e)
            raise HTTPException(status_code=503, detail="Internal Error")

    return templates.TemplateResponse(
        "author-add-exec.html", {"request": request, "author": res}
    )
