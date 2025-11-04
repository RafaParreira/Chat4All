from confluent_kafka import Consumer
import json
from db import SessionLocal, engine, Base
from models import Message

Base.metadata.create_all(bind=engine)

conf = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'chat4all-worker',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe(['messages'])

print("📡 Worker iniciado. Aguardando mensagens...")

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        print("⚠️ Erro:", msg.error())
        continue

    data = json.loads(msg.value().decode('utf-8'))
    db = SessionLocal()
    message = Message(
        message_id=data["message_id"],
        conversation_id=data["conversation_id"],
        sender=data["from_user"],
        receiver=json.dumps(data["to"]),
        payload=json.dumps(data["payload"]),
        status="SENT"
    )
    db.add(message)
    db.commit()
    db.close()

    print(f"💾 Mensagem {data['message_id']} salva no MySQL.")

    consumer.commit(asynchronous=False)
