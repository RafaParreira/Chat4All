import time
import uuid
import json
import socket
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError
from kafka_producer import send_message
from db import Base, engine, SessionLocal
from models import Message
from auth import create_token, get_current_user

app = FastAPI(title="Chat4All API", version="v1")


# ============================================================
# Funções auxiliares
# ============================================================
def wait_for_service(host: str, port: int, name: str, timeout: int = 60):
    """Tenta se conectar a um serviço até ele ficar disponível."""
    print(f"🔄 Aguardando {name} ({host}:{port}) ficar disponível...")
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"✅ {name} está acessível!")
                return
        except OSError:
            if time.time() - start_time > timeout:
                raise RuntimeError(f"⛔ Timeout ao aguardar {name}")
            time.sleep(2)


# ============================================================
# Inicialização segura
# ============================================================
@app.on_event("startup")
def startup_event():
    # Espera o Postgres subir
    wait_for_service("postgres", 5432, "PostgreSQL")

    # Espera o Kafka subir
    wait_for_service("kafka", 9092, "Kafka")

    # Tenta criar as tabelas
    for attempt in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Tabelas criadas (ou já existentes) no PostgreSQL.")
            break
        except OperationalError as e:
            print(f"⚠️ Tentativa {attempt+1}: Falha ao conectar no PostgreSQL ({e})")
            time.sleep(3)
    else:
        raise RuntimeError("⛔ Não foi possível conectar ao PostgreSQL após várias tentativas.")


# ============================================================
# Schemas
# ============================================================
class MessagePayload(BaseModel):
    type: str
    text: str


class MessageRequest(BaseModel):
    conversation_id: str
    from_user: str
    to: list[str]
    payload: MessagePayload

# rota para gerar token de teste
class TokenReq(BaseModel):
    user_id: str


# ============================================================
# Rotas
# ============================================================
@app.post("/v1/messages")
def post_message(msg: MessageRequest):
    """Recebe uma mensagem e envia para o Kafka."""
    message = {
        "message_id": str(uuid.uuid4()),
        "conversation_id": msg.conversation_id,
        "from_user": msg.from_user,
        "to": msg.to,
        "payload": msg.payload.dict()  # se estiver em Pydantic v2, pode usar .model_dump()
    }

    try:
        send_message("messages", message)
        print(f"📨 Mensagem enviada ao Kafka: {message}")
        return {"status": "accepted", "message_id": message["message_id"]}
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para Kafka: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar mensagem para o Kafka")

@app.post("/auth/token")
def issue_token(body: TokenReq):
    return {"access_token": create_token(body.user_id), "token_type": "bearer"}


@app.get("/v1/conversations/{conv_id}/messages")
def get_messages(conv_id: str):
    """Busca todas as mensagens de uma conversa no banco."""
    db = SessionLocal()
    try:
        rows = db.query(Message).filter(Message.conversation_id == conv_id).all()

        # Serialização explícita para evitar _sa_instance_state
        def to_dict(m: Message):
            return {
                "message_id": m.message_id,
                "conversation_id": m.conversation_id,
                "sender": m.sender,
                "receiver": m.receiver,
                "payload": m.payload,
                "status": m.status,
                # Se seu modelo tiver timestamps:
                # "created_at": m.created_at.isoformat() if getattr(m, "created_at", None) else None,
                # "updated_at": m.updated_at.isoformat() if getattr(m, "updated_at", None) else None,
            }

        return [to_dict(m) for m in rows]
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar mensagens")
    finally:
        db.close()
