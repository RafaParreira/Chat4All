from minio import Minio
from datetime import timedelta  # ainda pode ser útil se quiser manter presigned no futuro
import io

from config import (
    OBJECT_STORAGE_ENDPOINT,          # minio:9000  (interno, API/worker)
    OBJECT_STORAGE_ACCESS_KEY,
    OBJECT_STORAGE_SECRET_KEY,
    OBJECT_STORAGE_BUCKET_NAME,
    OBJECT_STORAGE_SECURE_BOOL,
)

# MinIO client interno (API -> MinIO dentro da rede Docker)
def get_minio_client_internal() -> Minio:
    return Minio(
        OBJECT_STORAGE_ENDPOINT,
        access_key=OBJECT_STORAGE_ACCESS_KEY,
        secret_key=OBJECT_STORAGE_SECRET_KEY,
        secure=OBJECT_STORAGE_SECURE_BOOL,
    )

def ensure_bucket_exists():
    client = get_minio_client_internal()
    found = client.bucket_exists(OBJECT_STORAGE_BUCKET_NAME)
    if not found:
        client.make_bucket(OBJECT_STORAGE_BUCKET_NAME)

# ---------------------------
#           UPLOAD
# ---------------------------
def upload_file_bytes(storage_key: str, data: bytes, content_type: str | None = None) -> None:
    client = get_minio_client_internal()
    ensure_bucket_exists()

    size = len(data)
    data_stream = io.BytesIO(data)

    client.put_object(
        OBJECT_STORAGE_BUCKET_NAME,
        storage_key,
        data_stream,
        length=size,
        content_type=content_type or "application/octet-stream",
    )

# ---------------------------
#      DOWNLOAD (stream)
# ---------------------------
def get_file_stream(storage_key: str):
    """
    Retorna um objeto de stream do MinIO para o arquivo dado.
    """
    client = get_minio_client_internal()
    # get_object retorna um HTTPResponse com .stream() / .read()
    return client.get_object(OBJECT_STORAGE_BUCKET_NAME, storage_key)
