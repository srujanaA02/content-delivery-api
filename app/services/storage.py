import os
import hashlib
import io
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

minio_client = Minio(
    f"{os.getenv('MINIO_ENDPOINT')}:{os.getenv('MINIO_PORT')}",
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False,
)

BUCKET = os.getenv("MINIO_BUCKET", "assets")


def init_bucket():
    if not minio_client.bucket_exists(BUCKET):
        minio_client.make_bucket(BUCKET)
        print("✅ MinIO bucket created")


def upload_file(file_bytes: bytes, object_key: str, mime_type: str):
    minio_client.put_object(
        BUCKET,
        object_key,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=mime_type,
    )


def get_file(object_key: str):
    response = minio_client.get_object(BUCKET, object_key)
    data = response.read()
    response.close()
    return data


def calculate_etag(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()