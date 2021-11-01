import glob
from minio import Minio, S3Error
import os

""" Minio Setup"""
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_HOST = os.getenv("MINIO_HOST", "minio:9000")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "thumbnail")


minio_client = Minio(
    MINIO_HOST,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


def initialize():
    found = minio_client.bucket_exists("paper")
    if not found:
        minio_client.make_bucket("paper")
    else:
        print("Bucket 'paper' already exists")

    found = minio_client.bucket_exists("thumbnail")
    if not found:
        minio_client.make_bucket("thumbnail")
    else:
        print("Bucket 'thumbnail' already exists")


def download_paper_handler(paper_uuid):
    try:
        response = minio_client.get_object(
            MINIO_BUCKET_NAME, f"{paper_uuid}-00.png")
        res = response.read()
        response.close()
        response.release_conn()
        return res

    except S3Error as e:
        print("Download exception: ", e)
        _status_code = 404 if e.code in (
            "NoSuchKey", "NoSuchBucket", "ResourceNotFound") else 503
        return _status_code, e


def upload_local_directory_to_minio(local_path, bucket_name, minio_path):
    assert os.path.isdir(local_path)

    for local_file in glob.glob(local_path + '/**'):
        local_file = local_file.replace(
            os.sep, "/")  # Replace \ with / on Windows
        if not os.path.isfile(local_file):
            upload_local_directory_to_minio(
                local_file,
                bucket_name,
                minio_path +
                "/" +
                os.path.basename(local_file))
        else:
            remote_path = os.path.join(
                minio_path, local_file[1 + len(local_path):])
            remote_path = remote_path.replace(
                os.sep, "/")  # Replace \ with / on Windows
            minio_client.fput_object(bucket_name, remote_path, local_file)
