import time
import uuid
import json
import socket
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError
from kafka_producer import send_message
from db import Base, engine, SessionLocal
from models import Message

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
    # Espera o MySQL subir
    wait_for_service("mysql", 3306, "MySQL")
    
    # Espera o Kafka subir
    wait_for_service("kafka", 9092, "Kafka")

    # Tenta criar as tabelas
    for attempt in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Tabelas criadas (ou já existentes).")
            break
        except OperationalError as e:
            print(f"⚠️ Tentativa {attempt+1}: Falha ao conectar no MySQL ({e})")
            time.sleep(3)
    else:
        raise RuntimeError("⛔ Não foi possível conectar ao MySQL após várias tentativas.")


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
        "payload": msg.payload.dict()
    }

    try:
        send_message("messages", message)
        print(f"📨 Mensagem enviada ao Kafka: {message}")
        return {"status": "accepted", "message_id": message["message_id"]}
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para Kafka: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar mensagem para o Kafka")


@app.get("/v1/conversations/{conv_id}/messages")
def get_messages(conv_id: str):
    """Busca todas as mensagens de uma conversa no banco."""
    db = SessionLocal()
    try:
        msgs = db.query(Message).filter(Message.conversation_id == conv_id).all()
        return [m.__dict__ for m in msgs]
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar mensagens")
    finally:
        db.close()
