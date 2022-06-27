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
    author_uuid_list: List,
    created_at: str,
    updated_at: str
):
    """ 論文情報の追加 """
    PAPER_UPLOAD_URL = f"{PAPER_URL}/paper"
    # todo: generate from openapi schema
    suff = ""
    if updated_at == "":
        updated_at = created_at
        suff = ".000Z"
    payload = {
        "author_uuid": author_uuid_list,
        "title": title,
        "label": label,
        "is_public": True,
        "created_at": created_at.split("+")[0] + ".000Z",
        "updated_at": updated_at.split("+")[0] + suff,
    }
    print(json.dumps(payload, indent=4, ensure_ascii=False))
    req = requests.post(PAPER_UPLOAD_URL, json=payload)
    print(req)
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


def paper_only_upload():
    with open('papers.json') as f:
        papers = json.load(f)
    # CDSL-TR-002: xxxxxxxxxxxxx
    mapping_table = {
        p["paper_id"]: p["paper_url_id"]
        for p in papers
    }

    req = requests.get(f"{PAPER_URL}/paper")
    assert req.status_code == 200
    res = req.json()

    for paper in res['papers']:
        try:
            paper_label = paper['label']
            paper_url_id = mapping_table[paper_label]
            paper_uuid = paper['uuid']

            PAPER_FILE_UPLOAD_URL = f"{PAPER_URL}/paper/{paper_uuid}/upload"
            print("PAPER_FILE_UPLOAD_URL:", PAPER_FILE_UPLOAD_URL)
            pdffile = {'file': (
                f"{paper_uuid}.pdf",
                open(f"pdf_files/{paper_url_id}.pdf", 'rb'),
                "application/pdf"
            )}
            req = requests.post(PAPER_FILE_UPLOAD_URL, files=pdffile)
            assert req.status_code == 200
        except Exception as e:
            print(e)
            print("Failed only upload:", paper)


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
        created_at = paper['created_at']
        updated_at = paper['updated_at']

        # print(authors, author_uuids)
        # print(title, paper_id, _datetime, paper_url_id)

        _paper_add(
            title=title,
            label=paper_id,
            pdf_file_path=f"pdf_files/{paper_url_id}.pdf",
            author_uuid_list=author_uuids,
            created_at=created_at,
            updated_at=updated_at,
        )


def thumbnail_add():
    req = requests.get(f"{PAPER_URL}/paper")
    assert req.status_code == 200
    res = req.json()
    for paper in res['papers']:
        try:
            paper_uuid = paper['uuid']
            req2 = requests.post(
                f"{THUMBNAIL_URL}/thumbnail/{paper_uuid}", data={})
            print(req2)
            print(paper['title'])
            assert req2.status_code == 200
        except Exception:
            print("Failed: thumbnail upload", paper)


def fulltext_add():
    req = requests.get(f"{PAPER_URL}/paper")
    assert req.status_code == 200
    res = req.json()
    for paper in res['papers']:
        try:
            paper_uuid = paper['uuid']
            req2 = requests.post(
                f"{FULLTEXT_URL}/fulltext/{paper_uuid}", data={})
            print(req2)
            print(paper['title'])
            assert req2.status_code == 200
        except Exception:
            print("Failed: fulltext upload", paper)


def main():
    # author_add_wrapper()
    # paper_add_wrapper()
    # paper_only_upload()
    thumbnail_add()
    # fulltext_add()


if __name__ == "__main__":
    main()
