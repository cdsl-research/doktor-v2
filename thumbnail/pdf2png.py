import os
import sys
import fitz
import requests


def _get_pdf_http(pdf_url: str):
    pdf_data = requests.get(pdf_url).content
    filename = pdf_url.split("/")[-1]
    dest_dir = './temp/' + filename
    os.makedirs(dest_dir, exist_ok=True)

    with open(dest_dir + "/" + filename, mode='wb') as f:  # wb でバイト型を書き込める
        f.write(pdf_data)
    return dest_dir + "/" + filename, dest_dir


def create(url):
    file, dest_dir = _get_pdf_http(url)

    with fitz.open(file) as doc:
        for i, page in enumerate(doc):
            for j, img in enumerate(page.getImageList()):
                x = doc.extractImage(img[0])
                name = os.path.join(dest_dir, f"{i:04}_{j:02}.{x['ext']}")
                with open(name, "wb") as ofh:
                    ofh.write(x['image'])

    return dest_dir


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
