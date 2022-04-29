import csv
import json
import os
import requests
from typing import List


AUTHOR_URL = os.getenv("AUTHOR_ENDPOINT", "http://localhost:4200")
PAPER_URL = os.getenv("PAPER_ENDPOINT", "http://localhost:4100")
THUMBNAIL_URL = os.getenv("THUMBNAIL_ENDPOINT", "http://localhost:4400")
FULLTEXT_URL = os.getenv("FULLTEXT_ENDPOINT", "http://localhost:4500")


def _author_add(
    first_name_ja: str,
    last_name_ja: str,
    first_name_en: str,
    last_name_en: str,
    joined_year: int,
    graduation: bool
):
    AUTHOR_UPLOAD_URL = f"{AUTHOR_URL}/author"
    # todo: generate from openapi schema
    payload = {
        "first_name_ja": first_name_ja,
        "middle_name_ja": "",
        "last_name_ja": last_name_ja,
        "first_name_en": first_name_en,
        "middle_name_en": "",
        "last_name_en": last_name_en,
        "joined_year": joined_year,
        "is_graduated": graduation
    }
    req = requests.post(AUTHOR_UPLOAD_URL, json=payload)
    print("Res:", req.text)
    assert req.status_code == 200


def _paper_add(
    title: str,
    label: str,
    pdf_file_path: str,
    author_uuid_list: List
):
    """ 論文情報の追加 """
    PAPER_UPLOAD_URL = f"{PAPER_URL}/paper"
    # todo: generate from openapi schema
    payload = {
        "author_uuid": author_uuid_list,
        "title": title,
        "keywords": [],
        "label": label,
        "categories_id": [],
        "abstract": "",
        "url": "",
        "thumbnail_url": "",
        "is_public": True
    }
    # print(payload)
    req = requests.post(PAPER_UPLOAD_URL, json=payload)
    assert req.status_code == 200
    res = req.json()
    paper_uuid = res["uuid"]

    """ 論文PDFの追加 """
    try:
        pdffile = {'file': (
            f"{paper_uuid}.pdf",
            open(pdf_file_path, 'rb'),
            "application/pdf"
        )}
    except Exception as e:
        print("Fail to upload:", e)
        return
    PAPER_FILE_UPLOAD_URL = f"{PAPER_URL}/paper/{paper_uuid}/upload"
    print("PAPER_FILE_UPLOAD_URL:", PAPER_FILE_UPLOAD_URL)
    req = requests.post(PAPER_FILE_UPLOAD_URL, files=pdffile)
    assert req.status_code == 200


def author_add_wrapper():
    """ 著者の追加 """
    with open("authors.json") as f:
        author_list = json.load(f)
    for author in author_list:
        print("Req:", author)
        _author_add(
            first_name_ja=author.get("first_name_ja"),
            last_name_ja=author.get("last_name_ja"),
            first_name_en=author.get("first_name_en"),
            last_name_en=author.get("last_name_en"),
            joined_year=author.get("joined_year"),
            graduation=author.get("graduation")
        )


def paper_add_wrapper():
    """ 論文の追加 """
    req = requests.get(f"{AUTHOR_URL}/author")
    author_list = req.json()
    # print(author_list)
    author_uuid_table = {
        author["last_name_ja"] + " " + author["first_name_ja"]: author["uuid"]
        for author in author_list
    }

    with open('papers.json') as f:
        papers = json.load(f)
    for paper in papers:
        authors = paper['author']
        author_uuids = [author_uuid_table.get(a) for a in authors]
        if None in author_uuids:
            print("Not found author:", authors, author_uuids)
        title = paper['title']
        paper_id = paper['paper_id']
        _datetime = paper['datetime']
        paper_url_id = paper['paper_url_id']
        # print(authors, author_uuids)
        # print(title, paper_id, _datetime, paper_url_id)

        _paper_add(
            title=title,
            label=paper_id,
            pdf_file_path=f"pdf_files/{paper_url_id}.pdf",
            author_uuid_list=author_uuids
        )


def thumbnail_add():
    req = requests.get(f"{PAPER_URL}/paper")
    assert req.status_code == 200
    res = req.json()
    for paper in res['papers']:
        paper_uuid = paper['uuid']
        req2 = requests.post(
            f"{THUMBNAIL_URL}/thumbnail/{paper_uuid}", data={})
        print(req2)
        assert req2.status_code == 200


def fulltext_add():
    req = requests.get(f"{PAPER_URL}/paper")
    assert req.status_code == 200
    res = req.json()
    for paper in res['papers']:
        paper_uuid = paper['uuid']
        req2 = requests.post(
            f"{FULLTEXT_URL}/fulltext/{paper_uuid}", data={})
        print(req2)
        assert req2.status_code == 200


def main():
    # author_add_wrapper()
    # paper_add_wrapper()
    # thumbnail_add()
    fulltext_add()


if __name__ == "__main__":
    main()
