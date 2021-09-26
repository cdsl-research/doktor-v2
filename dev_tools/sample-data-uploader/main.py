from io import BytesIO
import os
from typing import IO, BinaryIO
import requests

ENDPOINT_URL = os.getenv("FRONT_ADMIN_ENDPOINT", "http://localhost:4300")


def author_add(
    first_name_ja: str,
    last_name_ja: str,
    first_name_en: str,
    last_name_en: str,
    joined_year: int,
    graduation: bool
):
    AUTHOR_UPLOAD_URL = f"{ENDPOINT_URL}/author/add"
    # todo: generate from openapi schema
    payload = {
        "first_name_ja": first_name_ja,
        "last_name_ja": last_name_ja,
        "first_name_en": first_name_en,
        "last_name_en": last_name_en,
        "joined_year": joined_year,
        "graduation": graduation
    }
    req = requests.post(AUTHOR_UPLOAD_URL, data=payload)
    assert req.status_code == 200


def paper_add(
    title: str,
    label: str,
    pdf_file_path: str,
    author1_uuid: str,
    author2_uuid: str = "",
    author3_uuid: str = "",
):
    PAPER_UPLOAD_URL = f"{ENDPOINT_URL}/paper/add"
    # todo: generate from openapi schema
    pdffile = {'file': open(pdf_file_path, 'rb')}
    payload = {
        "title": title,
        "label": label,
        "author1": author1_uuid,
        "author2": author2_uuid,
        "author3": author3_uuid
    }
    req = requests.post(PAPER_UPLOAD_URL, data=payload, files=pdffile)
    assert req.status_code == 200


def main():
    # author_add()
    # paper_add
    pass


if __name__ == "__main__":
    main()
