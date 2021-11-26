import os
from typing import Union

import fitz
import requests


def fetch_pdf_http(pdf_url: str) -> Union[tuple[str, str]]:
    try:
        pdf_data = requests.get(pdf_url).content
    except Exception as e:
        raise e

    stored_filename = pdf_url.split("/")[-1]
    _paper_uuid = stored_filename.replace(".pdf", "")
    dest_dir = os.path.join('./temp/', _paper_uuid)
    os.makedirs(dest_dir, exist_ok=True)
    stored_path = os.path.join(dest_dir, stored_filename)
    with open(stored_path, mode='wb') as f:  # wb でバイト型を書き込める
        f.write(pdf_data)

    return stored_path, stored_filename


def convert_pdf_to_png(target_dir, pdf_filename: str) -> set:
    created_files = set()
    with fitz.open(pdf_filename) as doc:
        for i, page in enumerate(doc):
            for j, img in enumerate(page.getImageList()):
                x = doc.extractImage(img[0])
                image_filename = os.path.join(target_dir, f"{i:04}_{j:02}.{x['ext']}")
                created_files.add(image_filename)
                with open(image_filename, "wb") as ofh:
                    ofh.write(x['image'])

    return created_files


def get_first_page(url):
    dstdir = os.path.splitext(url)[0]
    os.makedirs(dstdir, exist_ok=True)
    with fitz.open(url) as doc:
        for i, page in enumerate(doc):
            for j, img in enumerate(page.getImageList()):
                x = doc.extractImage(img[0])
                name = os.path.join(dstdir, f"{i:04}_{j:02}.{x['ext']}")
                with open(name, "wb") as ofh:
                    ofh.write(x['image'])


# thumbnail("http://localhost:4190/paper/G2121007_TakamasaIijima%20%281%29.pdf")
