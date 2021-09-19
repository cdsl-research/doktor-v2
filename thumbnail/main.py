from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

import minio_manager


app = FastAPI()


class ThumbnailCreateUpdate(BaseModel):
    paper_uuid: List[UUID]
    paper_url: str


class PaperRead(BaseModel):
    paper_uuid: UUID
    thumbnail_url: str
    is_public: bool
    created_at: datetime
    updated_at: datetime
    # todo) reference_id: List[int]

# def minio_upload():
#
#     # Upload '/home/user/Photos/asiaphotos.zip' as object name
#     # 'asiaphotos-2015.zip' to bucket 'asiatrip'.
#     minio_client.fput_object(
#         "asiatrip", "asiaphotos-2015.zip", "/home/user/Photos/asiaphotos.zip",
#     )
#     print(
#         "'/home/user/Photos/asiaphotos.zip' is successfully uploaded as "
#         "object 'asiaphotos-2015.zip' to bucket 'asiatrip'."
#     )
#
# # except S3Error as exc:
# #     print("error occurred.", exc)


@app.get("/")
def root_handler():
    return {"Hello": "World"}


@app.get("/healthz")
def healthz_handler():
    return {"status": "ok", "message": "it works"}


@app.get("/topz")
def topz_handler():
    return {"resource": "busy"}


@app.post("/thumbnail")
def create_paper_handler(paper: ThumbnailCreateUpdate):
    json_paper = jsonable_encoder(paper)
    my_paper = {
        "uuid": uuid4(),
        "author_uuid": json_paper.get("author_uuid"),
        "title": json_paper.get("title"),
        "keywords": json_paper.get("keywords"),
        "label": json_paper.get("label"),
        "categories_id": json_paper.get("categories_id"),
        "abstract": json_paper.get("abstract"),
        "url": json_paper.get("url"),
        "thumbnail_url": json_paper.get("thumbnail_url"),
        "is_public": json_paper.get("is_public"),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    # insert_id = db["paper"].insert_one(my_paper).inserted_id
    # print("insert_id:", insert_id)
    return PaperRead(**my_paper)


@app.get("/hello")
def read_papers_handler():
    return {"body": "Hello"}


# @app.get("/thumbnail")
# def read_papers_handler():
#     return list(db["paper"].find({"is_public": True}, {'_id': 0}))
#


@app.post("/thumbnail/{paper_uuid}")
def process_paper_thumbnail(paper_uuid: UUID):
    import pdf2png
    folder = pdf2png.thumbnail(f"http://minio:9000/paper/{paper_uuid}.pdf")
    # try:
    result = minio_manager.upload_local_directory_to_minio(
        folder, bucket_name="thumbnail", minio_path=f"{paper_uuid}/")
    return result
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=e)

# @app.get("/thumbnail/{paper_uuid}")
# def read_paper_handler(paper_uuid: UUID):
#     entry = db["paper"].find_one({"uuid": paper_uuid, "is_public": True}, {'_id': 0})
#     if entry:
#         return entry
#     else:
#         raise HTTPException(status_code=404, detail="Not Found")


@app.get("/thumbnail/{paper_uuid}")
def get_thumbnail(paper_uuid: UUID):
    # try:
    res = minio_manager.download_paper_handler(paper_uuid)
    return Response(content=res, media_type="image/png")

    # except:
    #     raise HTTPException(status_code=status_code, detail=str(e.message))


@app.put("/thumbnail/{paper_uuid}")
def update_paper_handler(paper_uuid: UUID, paper: ThumbnailCreateUpdate):
    json_paper = jsonable_encoder(paper)
    my_paper = {
        "uuid": paper_uuid,
        "author_uuid": json_paper.get("author_uuid"),
        "title": json_paper.get("title"),
        "keywords": json_paper.get("keywords"),
        "label": json_paper.get("label"),
        "categories_id": json_paper.get("categories_id"),
        "abstract": json_paper.get("abstract"),
        "url": json_paper.get("url"),
        "thumbnail_url": json_paper.get("thumbnail_url"),
        "is_public": json_paper.get("is_public"),
        "created_at": datetime.now(),  # todo: get stored data
        "updated_at": datetime.now()
    }
    return PaperRead(**my_paper)


if __name__ == "__main__":
    minio_manager.initialize()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0")
