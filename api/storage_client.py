from minio import Minio
from datetime import timedelta
import io

from config import (
    OBJECT_STORAGE_ENDPOINT,          # minio:9000  (interno, API/worker)
    OBJECT_STORAGE_PUBLIC_ENDPOINT,   # localhost:9000 (externo, navegador)
    OBJECT_STORAGE_ACCESS_KEY,
    OBJECT_STORAGE_SECRET_KEY,
    OBJECT_STORAGE_BUCKET_NAME,
    OBJECT_STORAGE_SECURE_BOOL,
)

# 🚀 MinIO client interno (API -> MinIO dentro da rede Docker)
def get_minio_client_internal() -> Minio:
    return Minio(
        OBJECT_STORAGE_ENDPOINT,
        access_key=OBJECT_STORAGE_ACCESS_KEY,
        secret_key=OBJECT_STORAGE_SECRET_KEY,
        secure=OBJECT_STORAGE_SECURE_BOOL,
    )

# 🌍 MinIO client para URL pública
def get_minio_client_public() -> Minio:
    return Minio(
        OBJECT_STORAGE_PUBLIC_ENDPOINT,
        access_key=OBJECT_STORAGE_ACCESS_KEY,
        secret_key=OBJECT_STORAGE_SECRET_KEY,
        secure=OBJECT_STORAGE_SECURE_BOOL,
    )

def ensure_bucket_exists():
    client = get_minio_client_internal()
    if not client.bucket_exists(OBJECT_STORAGE_BUCKET_NAME):
        client.make_bucket(OBJECT_STORAGE_BUCKET_NAME)

# ---------------------------
#           UPLOAD
# ---------------------------
def upload_file_bytes(storage_key: str, data: bytes, content_type: str | None = None) -> None:
    client = get_minio_client_internal()
    ensure_bucket_exists()

    client.put_object(
        OBJECT_STORAGE_BUCKET_NAME,
        storage_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type or "application/octet-stream",
    )

# ---------------------------
#         DOWNLOAD URL
# ---------------------------
def generate_presigned_download_url(storage_key: str, expires_seconds: int = 300) -> str:
    # Para gerar o link público, usamos o endpoint interno
    client = get_minio_client_internal()

    return client.presigned_get_object(
        OBJECT_STORAGE_BUCKET_NAME,
        storage_key,
        expires=timedelta(seconds=expires_seconds),
    )
