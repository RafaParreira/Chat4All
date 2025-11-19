from minio import Minio
from minio.error import S3Error
import io

from config import (
    OBJECT_STORAGE_ENDPOINT,
    OBJECT_STORAGE_ACCESS_KEY,
    OBJECT_STORAGE_SECRET_KEY,
    OBJECT_STORAGE_BUCKET_NAME,
    OBJECT_STORAGE_SECURE_BOOL,
)


def get_minio_client() -> Minio:
    return Minio(
        OBJECT_STORAGE_ENDPOINT,
        access_key=OBJECT_STORAGE_ACCESS_KEY,
        secret_key=OBJECT_STORAGE_SECRET_KEY,
        secure=OBJECT_STORAGE_SECURE_BOOL,
    )


def ensure_bucket_exists():
    client = get_minio_client()
    found = client.bucket_exists(OBJECT_STORAGE_BUCKET_NAME)
    if not found:
        client.make_bucket(OBJECT_STORAGE_BUCKET_NAME)


# Faz upload simples (não multipart) de um arquivo em memória.
def upload_file_bytes(storage_key: str, data: bytes, content_type: str | None = None) -> None:
   
    client = get_minio_client()
    ensure_bucket_exists()

    size = len(data)
    data_stream = io.BytesIO(data)  # <-- transforma bytes em um "arquivo" em memória

    client.put_object(
        OBJECT_STORAGE_BUCKET_NAME,
        storage_key,
        data_stream,
        length=size,
        content_type=content_type or "application/octet-stream",
    )
