import os
import sys
import fitz
import requests


def get_pdf(url):
    urlData = requests.get(url).content
    filename = url.split("/")[4]
    dstdir = './temp/' + filename
    os.makedirs(dstdir, exist_ok=True)

    with open(dstdir + "/" + filename, mode='wb') as f:  # wb でバイト型を書き込める
        f.write(urlData)
    return dstdir + "/" + filename, dstdir


def thumbnail(url):
    file, dstdir = get_pdf(url)

    with fitz.open(file) as doc:
        for i, page in enumerate(doc):
            for j, img in enumerate(page.getImageList()):
                x = doc.extractImage(img[0])
                name = os.path.join(dstdir, f"{i:04}_{j:02}.{x['ext']}")
                with open(name, "wb") as ofh:
                    ofh.write(x['image'])

    return dstdir


def first_page(url):
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
