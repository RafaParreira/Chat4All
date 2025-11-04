from fastapi import FastAPI
from pydantic import BaseModel
from kafka_producer import send_message
from db import Base, engine, SessionLocal
from models import Message
import uuid, json

app = FastAPI(title="Chat4All API", version="v1")

# Cria as tabelas no MySQL
Base.metadata.create_all(bind=engine)

class MessagePayload(BaseModel):
    type: str
    text: str

class MessageRequest(BaseModel):
    conversation_id: str
    from_user: str
    to: list[str]
    payload: MessagePayload

@app.post("/v1/messages")
def post_message(msg: MessageRequest):
    message = {
        "message_id": str(uuid.uuid4()),
        "conversation_id": msg.conversation_id,
        "from_user": msg.from_user,
        "to": msg.to,
        "payload": msg.payload.dict()
    }
    send_message("messages", message)
    return {"status": "accepted", "message_id": message["message_id"]}

@app.get("/v1/conversations/{conv_id}/messages")
def get_messages(conv_id: str):
    db = SessionLocal()
    msgs = db.query(Message).filter(Message.conversation_id == conv_id).all()
    return [m.__dict__ for m in msgs]
