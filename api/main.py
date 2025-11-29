from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File as UploadFileType, Form, Request
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, StreamingResponse, Response
from starlette.background import BackgroundTask
from datetime import datetime
from typing import List
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import hashlib
import uuid
import time
import threading
import psutil

from sqlalchemy.orm import Session

from db import Base, engine, get_db
from models import User, Room, Message, File as FileModel
from schemas import (
    UserCreate,
    UserOut,
    RoomCreate,
    RoomOut,
    MessageCreate,
    MessageOut,
    FileOut,
     FileDownloadURLOut,
)
from kafka_producer import send_message_to_kafka
from storage_client import upload_file_bytes, get_file_stream

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat4All API")


# ============================
#   Métricas Prometheus API
# ============================
API_REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "Latência das requisições da API em segundos",
    ["method", "path"],
)

API_ERRORS_TOTAL = Counter(
    "api_errors_total",
    "Total de respostas 5xx retornadas pela API",
)

API_CPU_PERCENT = Gauge(
    "api_cpu_percent",
    "Uso de CPU da API em porcentagem",
)

API_MEMORY_PERCENT = Gauge(
    "api_memory_percent",
    "Uso de memória da API em porcentagem",
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        # conta erros 5xx
        API_ERRORS_TOTAL.inc()
        raise
    finally:
        elapsed = time.time() - start
        # usa apenas o path bruto (sem querystring)
        API_REQUEST_LATENCY.labels(
            method=request.method,
            path=request.url.path,
        ).observe(elapsed)
    return response


def _collect_resource_usage():
    """
    Coleta periódica de CPU e memória da API.
    Roda em uma thread em background.
    """
    while True:
        # interval=None -> usa a média desde a última chamada,
        # para não bloquear a thread por 1s
        API_CPU_PERCENT.set(psutil.cpu_percent(interval=None))
        API_MEMORY_PERCENT.set(psutil.virtual_memory().percent)
        time.sleep(5)


@app.on_event("startup")
def start_metrics_background():
    # não atrapalha o startup da API
    t = threading.Thread(target=_collect_resource_usage, daemon=True)
    t.start()


# ---- ARMAZENAMENTO EM MEMÓRIA PARA TESTE ----
# in_memory_messages: list[dict] = []
# in_memory_next_id = 1


# ---- STATIC FRONTEND ----
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------- USERS ----------
@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username já em uso.",
        )
    user = User(username=payload.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=UserOut)
def root():
    # redireciona para a página HTML
    return RedirectResponse(url="/static/index.html")

def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


# ---------- ROOMS ----------
@app.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    existing = db.query(Room).filter(Room.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sala já existe.",
        )
    room = Room(name=payload.name)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

# ---------- linha de código para teste em API depois que o BD estiver implementado voltar ao app.post e app.get comentados ----------
# @app.post(
#     "/messages",
#     response_model=MessageOut,
#     summary="[TESTE] Enviar mensagem (memória, sem Kafka/DB)",
# )
# def send_message_test(payload: MessageCreate):
#     global in_memory_next_id

#     msg = MessageOut(
#         id=in_memory_next_id,
#         room_id=payload.room_id,
#         sender_id=payload.sender_id,
#         content=payload.content,
#         created_at=datetime.utcnow(),
#     )

#     in_memory_messages.append(msg)
#     in_memory_next_id += 1
#     return msg

@app.post("/v1/files/simple-upload", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def simple_file_upload(
    uploader_id: int = Form(...),
    room_id: int = Form(...),
    upload: UploadFile = UploadFileType(...),
    db: Session = Depends(get_db),
):
   
    # valida usuário e sala
    user = db.get(User, uploader_id)
    if not user:
        raise HTTPException(status_code=404, detail="Uploader (usuário) não encontrado")

    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    size_bytes = len(data)
    checksum = hashlib.sha256(data).hexdigest()
    file_id = str(uuid.uuid4())

    # chave no storage (você pode mudar o layout se quiser)
    storage_key = f"rooms/{room_id}/files/{file_id}"

    # upload pro MinIO
    upload_file_bytes(storage_key=storage_key, data=data, content_type=upload.content_type)

    # registra no banco
    file_obj = FileModel(
        id=file_id,
        filename=upload.filename,
        content_type=upload.content_type,
        size_bytes=size_bytes,
        checksum=checksum,
        storage_key=storage_key,
        uploader_id=uploader_id,
        room_id=room_id,
    )

    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)

    return file_obj


# @app.get(
#     "/v1/files/{file_id}/download-url",
#     response_model=FileDownloadURLOut,
#     status_code=status.HTTP_200_OK,
# )
# def get_file_download_url(
#     file_id: str,
#     db: Session = Depends(get_db),
# ):
#     file_obj = db.get(FileModel, file_id)
#     if not file_obj:
#         raise HTTPException(status_code=404, detail="Arquivo não encontrado")

#     # aqui poderia ter regra de permissão (ex: usuário precisa estar na mesma sala)
#     # por enquanto, deixamos aberto apenas para teste.

#     expires_in = 300  # segundos (5 minutos)
#     url = generate_presigned_download_url(file_obj.storage_key, expires_seconds=expires_in)

#     return FileDownloadURLOut(
#         file_id=file_id,
#         url=url,
#         expires_in=expires_in,
#     )


@app.get("/v1/files/{file_id}/download")
def download_file_v1(file_id: str, db: Session = Depends(get_db)):
    """
    Faz o download do arquivo passando pela API.
    O navegador acessa localhost:8000 e a API busca o arquivo no MinIO.
    """
    file_obj = db.get(FileModel, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    # stream do MinIO
    obj = get_file_stream(file_obj.storage_key)

    # gera um iterador de chunks
    def iter_stream():
        for data in obj.stream(32 * 1024):
            yield data

    # garante que o stream será fechado depois
    background = BackgroundTask(obj.close)

    return StreamingResponse(
        iter_stream(),
        media_type=file_obj.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file_obj.filename}"'
        },
        background=background,
    )



@app.get("/rooms/{room_id}", response_model=RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    return room


# @app.get(
#     "/rooms/{room_id}/messages",
#     response_model=List[MessageOut],
#     summary="[TESTE] Listar mensagens (memória, sem Kafka/DB)",
# )
# def list_messages_test(room_id: int):
#     return [m for m in in_memory_messages if m.room_id == room_id]

# ---------- MESSAGES ----------
@app.post(
    "/messages",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Envia mensagem (vai para Kafka)",
)
def send_message(payload: MessageCreate, db: Session = Depends(get_db)):
    # valida se usuário e sala existem
    room = db.get(Room, payload.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    user = db.get(User, payload.sender_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # publica no Kafka – persistência será feita pelo worker
    send_message_to_kafka(payload.model_dump())
    return {"status": "queued"}


@app.get("/rooms/{room_id}/messages", response_model=list[MessageOut])
def list_messages(room_id: int, db: Session = Depends(get_db), limit: int = 50):
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    messages = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    # retorna do mais recente para o mais antigo (você pode inverter se preferir)
    return list(reversed(messages))

@app.get("/metrics")
def metrics():
    """
    Endpoint padrão Prometheus para coletar métricas da API.
    """
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)
