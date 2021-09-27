import csv
import json
import os
import requests
from typing import List


AUTHOR_URL = os.getenv("AUTHOR_ENDPOINT", "http://localhost:4200")
PAPER_URL = os.getenv("PAPER_ENDPOINT", "http://localhost:4100")


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
    pdffile = {'file': (
        f"{paper_uuid}.pdf", 
        open(pdf_file_path, 'rb'),
        "application/pdf"
    )}
    PAPER_FILE_UPLOAD_URL = f"{PAPER_URL}/paper/{paper_uuid}/upload"
    print("PAPER_FILE_UPLOAD_URL:", PAPER_FILE_UPLOAD_URL)
    req = requests.post(PAPER_FILE_UPLOAD_URL, files=pdffile)
    assert req.status_code == 200



def author_add_wrapper():
    """ 著者の追加 """
    with open("author.json") as f:
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
        (author["last_name_ja"], author["first_name_ja"]): author["uuid"]
        for author in author_list
    }

    with open('paper.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile)
        next(spamreader)
        for row in spamreader:
            # (lastname, firstname)
            author1 = (row[0], row[1])
            uuid1 = author_uuid_table.get(author1)
            author2 = (row[2], row[3])
            uuid2 = author_uuid_table.get(author2)
            author3 = (row[4], row[5])
            uuid3 = author_uuid_table.get(author3)
            uuid_list = list(filter(None, [uuid1, uuid2, uuid3]))
            _paper_add(
                title=row[6],
                label=row[7],
                pdf_file_path=f"pdf_files/{row[7]}.pdf",
                author_uuid_list=uuid_list
            )


def main():
    author_add_wrapper()
    paper_add_wrapper()


if __name__ == "__main__":
    main()
