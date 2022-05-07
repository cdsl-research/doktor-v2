import asyncio
import os
import re
from dataclasses import dataclass
from datetime import datetime as dt
from typing import Tuple
from uuid import UUID

import aiohttp
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

SVC_PAPER_HOST = os.getenv("SERVICE_PAPER_HOST", "paper-app")
SVC_PAPER_PORT = os.getenv("SERVICE_PAPER_PORT", "8000")
SVC_AUTHOR_HOST = os.getenv("SERVICE_AUTHOR_HOST", "author-app")
SVC_AUTHOR_PORT = os.getenv("SERVICE_AUTHOR_PORT", "8000")
SVC_THUMBNAIL_HOST = os.getenv("SERVICE_THUMBNAIL_HOST", "thumbnail-app")
SVC_THUMBNAIL_PORT = os.getenv("SERVICE_THUMBNAIL_PORT", "8000")
SVC_FULLTEXT_HOST = os.getenv("SERVICE_FULLTEXT_HOST", "fulltext-app")
SVC_FULLTEXT_PORT = os.getenv("SERVICE_FULLTEXT_PORT", "8000")
REQ_TIMEOUT_SEC = int(os.getenv("REQUEST_TIMEOUT_SEC", 5))

TIMEOUT = aiohttp.ClientTimeout(total=REQ_TIMEOUT_SEC)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@dataclass
class FetchUrl:
    url: str = ""
    require: bool = False


# 日付のフォーマットを修正
def reformat_datetime(raw_str: str) -> str:
    _created = dt.fromisoformat(raw_str)
    return _created.strftime("%b. %d, %Y")


# ファイル取得
async def fetch_file(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()
        return await response.read()


# マイクロサービス呼び出し: Worker
async def fetch(session: aiohttp.ClientSession, url: str, require: bool):
    try:
        async with session.get(url) as response:
            if response.status >= 300:
                response.raise_for_status()
            return await response.json()
    except Exception as e:
        if require:
            raise e
        else:
            print("Fetch exception:", "url=", url)


# マイクロサービス呼び出し: Master
# Masterから複数のWorkerを呼び出す．
async def fetch_all(session: aiohttp.ClientSession, urls: Tuple[FetchUrl]):
    tasks = []
    for url in urls:
        task = asyncio.create_task(
            fetch(session=session, url=url.url, require=url.require))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    print("Error: ", exc.detail)
    message = "システムの内部で問題が発生しました．"
    if exc.status_code == 404:
        message = "コンテンツが見つかりません．"
    elif exc.status_code == 400:
        message = "リクエストが不正です．"

    return templates.TemplateResponse("error.html", {
        "message": message,
        "request": request
    }, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("Error: ", exc.detail)
    templates.TemplateResponse("error.html", {
        "message": "不正なリクエストです．",
        "request": request
    }, status_code=400)


@app.get("/", response_class=HTMLResponse)
async def top_handler(request: Request, keyword: str = ""):
    striped_keyword = ""
    if keyword:
        # スペースを削除
        striped_keyword = keyword.strip().replace("　", "")
        validate_word = re.match('^[0-9a-zA-Zあ-んア-ン一-鿐ー]+$', striped_keyword)
        if validate_word is None:
            raise HTTPException(status_code=400, detail="不正なキーワードです．")

    urls = (
        # 論文タイトルの検索
        FetchUrl(
            url=f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper",
            require=True),
        # 著者の一覧
        FetchUrl(
            url=f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author",
            require=True),
        # 全文の検索
        FetchUrl(
            url=f"http://{SVC_FULLTEXT_HOST}:{SVC_FULLTEXT_PORT}/fulltext?keyword={striped_keyword}",
            require=False),
        # 著者名の検索
        FetchUrl(
            url=f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author?name={striped_keyword}",
            require=False),
    )
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        try:
            json_raw = await fetch_all(session, urls)
        except aiohttp.ClientResponseError as e:
            print("Top Error 1:", e)
            if e.code == 404:
                raise HTTPException(status_code=404)
            raise HTTPException(status_code=503)
        except Exception as e:
            print("Top Error 2:", e)
            raise HTTPException(status_code=503)

    res_paper = json_raw[0]['papers']
    res_author = json_raw[1]
    res_fulltext = json_raw[2]
    res_author_search = json_raw[3]

    # 論文タイトルの検索
    found_papers = []
    for rp in res_paper:
        if striped_keyword in rp['title']:
            found_papers.append(rp)
    # print(found_papers)

    # 全文の検索
    if res_fulltext:
        for rf in res_fulltext:
            found_ = list(
                filter(lambda x: rf['paper_uuid'] == x['uuid'], res_paper))[0]
            if found_ in found_papers:
                continue
            found_papers.append(found_)
        # print(found_papers)
    # print(json.dumps(found_papers, indent=4, ensure_ascii=False))

    paper_details = []
    for rp in found_papers:  # 論文を選択
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

    # 著者名の検索
    author_details = []
    if keyword:
        for author in res_author_search:
            display_name = author.get('last_name_ja') + " " + \
                author.get('first_name_ja')
            author_details.append({
                "name": display_name,
                "uuid": author["uuid"]
            })

    return templates.TemplateResponse("top.html", {
        "request": request,
        "papers": paper_details,
        "authors": author_details,
        "search_keyword": striped_keyword
    })


@app.get("/paper/{paper_uuid}", response_class=HTMLResponse)
async def paper_handler(paper_uuid: UUID, request: Request):
    urls = (
        FetchUrl(
            url=f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author",
            require=True),
        FetchUrl(
            url=f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper/{paper_uuid}",
            require=True),
        FetchUrl(
            url=f"http://{SVC_THUMBNAIL_HOST}:{SVC_THUMBNAIL_PORT}/thumbnail/{paper_uuid}",
            require=False),
        FetchUrl(
            url=f"http://{SVC_FULLTEXT_HOST}:{SVC_FULLTEXT_PORT}/fulltext/{paper_uuid}",
            require=False))
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        try:
            json_raw = await fetch_all(session=session, urls=urls)
        except aiohttp.ClientResponseError as e:
            print("Paper Single View Fetch Error 1:", e)
            if e.code == 404:
                raise HTTPException(status_code=404)
            raise HTTPException(status_code=503)
        except Exception as e:
            print("Paper Single View Fetch Error 2:", e)
            raise HTTPException(status_code=503)

    res_author = json_raw[0]
    res_paper_me = json_raw[1]
    res_thumbnail = json_raw[2]
    res_fulltext = json_raw[3]

    # 著者の取得
    found_author = []
    for uuid in res_paper_me["author_uuid"]:
        try:
            candidates = filter(lambda x: uuid == x.get("uuid"), res_author)
            candidates_lst = list(candidates)
            if len(candidates_lst) > 0:
                author = candidates_lst[0]
                found_author.append(author)
        except Exception as e:
            print("Paper Single View Author Error:", e)
            continue

    # サムネイル一覧
    prefix = f"/thumbnail/{paper_uuid}/"
    try:
        thumbnail_list = map(lambda x: prefix + x, res_thumbnail['images'])
    except Exception:
        thumbnail_list = []

    paper_details = {
        "uuid": res_paper_me.get("uuid"),
        "title": res_paper_me.get("title"),
        "author": [{
            "name": author.get("last_name_ja") + author.get("first_name_ja"),
            "uuid": author.get("uuid")
        } for author in found_author],
        "label": res_paper_me.get("label"),
        "created_at": reformat_datetime(res_paper_me.get("created_at")),
        "updated_at": reformat_datetime(res_paper_me.get("updated_at")),
    }

    # 全文
    try:
        first_page = list(
            filter(lambda x: x['page_number'] == 0, res_fulltext))[0]
        first_page_text = first_page['text']
        # 「概要：」が3文字分あるため+3
        abstract_starts = first_page_text.find("概要：") + 3
        first_page_300 = first_page_text[abstract_starts:abstract_starts + 300]
    except Exception:
        first_page_300 = ""

    return templates.TemplateResponse(
        "paper.html", {
            "request": request,
            "paper": paper_details,
            "page_title": f"{paper_details['title']}",
            "image_urls": thumbnail_list,
            "abstract": first_page_300
        })


@app.get("/paper/{paper_uuid}/download", response_class=Response)
async def paper_download_handler(paper_uuid: UUID, request: Request):
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        url = f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper/{paper_uuid}/download"
        try:
            res_pdf = await fetch_file(session, url)
        except aiohttp.ClientResponseError as e:
            print("Paper Download Error 1:", e)
            if e.code == 404:
                raise HTTPException(status_code=404)
            raise HTTPException(status_code=503)
        except Exception as e:
            print("Paper Download Error 2:", e)
            raise HTTPException(status_code=503)

    return Response(content=res_pdf, media_type="application/pdf")


@app.get("/author/{author_uuid}", response_class=HTMLResponse)
async def author_handler(author_uuid: UUID, request: Request):
    urls = (
        FetchUrl(
            url=f"http://{SVC_PAPER_HOST}:{SVC_PAPER_PORT}/paper",
            require=True),
        FetchUrl(
            url=f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author",
            require=True),
        FetchUrl(
            url=f"http://{SVC_AUTHOR_HOST}:{SVC_AUTHOR_PORT}/author/{author_uuid}",
            require=True))
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        try:
            json_res = await fetch_all(session, urls)
        except aiohttp.ClientResponseError as e:
            print("Author Single View Error 1:", e)
            if e.code == 404:
                raise HTTPException(status_code=404)
            raise HTTPException(status_code=503)
        except Exception as e:
            print("Author Single View Error 2:", e)
            raise HTTPException(status_code=503)

    res_paper = json_res[0]['papers']
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


@app.get("/thumbnail/{paper_uuid}/{image_id}")
async def thumbnail_handler(paper_uuid: UUID, image_id: str):
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        url = (f"http://{SVC_THUMBNAIL_HOST}:{SVC_THUMBNAIL_PORT}"
               f"/thumbnail/{paper_uuid}/{image_id}")
        try:
            res_img = await fetch_file(session, url)
        except aiohttp.ClientResponseError as e:
            print("Thumbnail Download Error 1:", e)
            if e.code == 404:
                # raise HTTPException(status_code=404)
                return FileResponse("assets/404.png")
            raise HTTPException(status_code=503)
        except Exception as e:
            print("Thumbnail Download Error 2:", e)
            raise HTTPException(status_code=503)

    return Response(content=res_img, media_type="image/png")
