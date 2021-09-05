import asyncio
import json

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
        concat_author = ", ".join(fa.get("last_name_ja") + fa.get("first_name_ja") for fa in found_author)
        paper_details.append({
            "title": rp.get("title", "No Title"),
            "author": concat_author,
            "label": rp.get("label", "No Label"),
            "created_at": rp.get("created_at")
        })
    # sample_data = [{"title": "my title", "author": "my author", "label": "my label", "created_at": "2021/02/03"}]
    return templates.TemplateResponse("top.html", {"request": request, "papers": paper_details})
