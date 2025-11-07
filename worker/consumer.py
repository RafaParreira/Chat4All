import os
import json
import signal
import sys
from time import sleep
from confluent_kafka import Consumer
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from db import SessionLocal, engine, Base
from models import Message

# Garante que a tabela exista
Base.metadata.create_all(bind=engine)

# Config do Kafka por env (fallbacks para seu compose)
conf = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "group.id": os.getenv("KAFKA_GROUP_ID", "chat4all-worker"),
    "auto.offset.reset": os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
    # opcional: 'enable.auto.commit': False  # manteremos commit manual explícito
}
consumer = Consumer(conf)
consumer.subscribe([os.getenv("KAFKA_TOPIC", "messages")])

running = True
def handle_sigterm(sig, frame):
    global running
    running = False
signal.signal(signal.SIGINT, handle_sigterm)
signal.signal(signal.SIGTERM, handle_sigterm)

print("📡 Worker iniciado. Aguardando mensagens...")

try:
    while running:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("⚠️ Erro no Kafka:", msg.error())
            continue

        try:
            data = json.loads(msg.value().decode("utf-8"))
        except Exception as e:
            print("⚠️ Erro ao decodificar JSON:", e)
            # commit mesmo assim para não ficar travado em mensagem inválida
            consumer.commit(asynchronous=False)
            continue

        # Monta campos (preservando seu contrato atual)
        record = {
            "message_id":      data["message_id"],
            "conversation_id": data["conversation_id"],
            "sender":          data.get("from_user", ""),
            "receiver":        json.dumps(data.get("to", "")),
            "payload":         json.dumps(data.get("payload", {})),
            "status":          "SENT",
        }

        # Upsert idempotente
        try:
            with SessionLocal() as db:  # type: Session
                stmt = (
                    insert(Message)
                    .values(**record)
                    .on_conflict_do_update(
                        index_elements=[Message.message_id],
                        set_={
                            "conversation_id": record["conversation_id"],
                            "sender": record["sender"],
                            "receiver": record["receiver"],
                            "payload": record["payload"],
                            "status": record["status"],
                        },
                    )
                )
                db.execute(stmt)
                db.commit()

                # --- (Opcional) simular entrega e marcar DELIVERED ---
                # sleep(0.2)
                # db.query(Message).filter(
                #     Message.message_id == record["message_id"]
                # ).update({"status": "DELIVERED"})
                # db.commit()
                # -----------------------------------------------------

            print(f"💾 Mensagem {record['message_id']} salva/atualizada no PostgreSQL.")
            consumer.commit(asynchronous=False)

        except Exception as e:
            print("❌ Erro ao salvar no PostgreSQL:", e)
            # Não faz commit do offset para tentar reprocessar
            # (em produção, considere DLQ / retries exponenciais)
except Exception as e:
    print("❌ Erro inesperado no loop do worker:", e)
finally:
    try:
        consumer.close()
    except Exception:
        pass
    print("👋 Worker finalizado.")
