import json
import os
import requests

AUTHOR_URL = os.getenv("AUTHOR_ENDPOINT", "http://localhost:4200")
PAPER_URL = os.getenv("PAPER_ENDPOINT", "http://localhost:4100")


def author_add(
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


def paper_add(
    title: str,
    label: str,
    pdf_file_path: str,
    author1_uuid: str,
    author2_uuid: str = "",
    author3_uuid: str = "",
):
    PAPER_UPLOAD_URL = f"{ENDPOINT_URL}/paper"
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
    with open("author.json") as f:
        author_list = json.load(f)
    for author in author_list:
        print("Req:", author)
        author_add(
            first_name_ja=author.get("first_name_ja"),
            last_name_ja=author.get("last_name_ja"),
            first_name_en=author.get("first_name_en"),
            last_name_en=author.get("last_name_en"),
            joined_year=author.get("joined_year"),
            graduation=author.get("graduation")
        )


if __name__ == "__main__":
    main()
