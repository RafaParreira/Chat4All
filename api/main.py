from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from datetime import datetime
from typing import List


from db import Base, engine, get_db
from models import User, Room, Message
from schemas import (
    UserCreate,
    UserOut,
    RoomCreate,
    RoomOut,
    MessageCreate,
    MessageOut,
)
from kafka_producer import send_message_to_kafka

# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat4All API")


# ---- ARMAZENAMENTO EM MEMÓRIA PARA TESTE ----
in_memory_messages: list[dict] = []
in_memory_next_id = 1


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
# @app.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
# def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
#     existing = db.query(Room).filter(Room.name == payload.name).first()
#     if existing:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Sala já existe.",
#         )
#     room = Room(name=payload.name)
#     db.add(room)
#     db.commit()
#     db.refresh(room)
#     return room

# ---------- linha de código para teste em API depois que o BD estiver implementado voltar ao app.post e app.get comentados ----------
@app.post(
    "/test/messages",
    response_model=MessageOut,
    summary="[TESTE] Enviar mensagem (memória, sem Kafka/DB)",
)
def send_message_test(payload: MessageCreate):
    global in_memory_next_id

    msg = MessageOut(
        id=in_memory_next_id,
        room_id=payload.room_id,
        sender_id=payload.sender_id,
        content=payload.content,
        created_at=datetime.utcnow(),
    )

    in_memory_messages.append(msg)
    in_memory_next_id += 1
    return msg




# @app.get("/rooms/{room_id}", response_model=RoomOut)
# def get_room(room_id: int, db: Session = Depends(get_db)):
#     room = db.get(Room, room_id)
#     if not room:
#         raise HTTPException(status_code=404, detail="Sala não encontrada")
#     return room


@app.get(
    "/test/rooms/{room_id}/messages",
    response_model=List[MessageOut],
    summary="[TESTE] Listar mensagens (memória, sem Kafka/DB)",
)
def list_messages_test(room_id: int):
    return [m for m in in_memory_messages if m.room_id == room_id]

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
