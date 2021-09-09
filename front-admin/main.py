import asyncio
import os

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

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
    return {"hello": "world"}
    # sample_data = [{"title": "my title", "author": "my author", "label": "my label", "created_at": "2021/02/03"}]
    #return templates.TemplateResponse(
    #    "top.html", {"request": request, "papers": paper_details})


@app.get("/paper")
def read_paper_list_handler(request: Request):
    return templates.TemplateResponse("paper.html", {"request": request})


@app.get("/paper/add")
def add_paper_handler(request: Request):
    return templates.TemplateResponse("paper-add.html", {"request": request})

@app.get("/author")
def read_author_list_handler(request: Request):
    return templates.TemplateResponse("author.html", {"request": request})

@app.get("/author/add")
def add_author_handler(request: Request):
    return templates.TemplateResponse("author-add.html", {"request": request})
