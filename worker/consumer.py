import json
import time

from confluent_kafka import Consumer, KafkaError
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CHAT_TOPIC, KAFKA_GROUP_ID
from db import SessionLocal, engine, Base
from models import Message


def wait_for_db(max_retries: int = 30, delay: int = 2):
    """Tenta conectar no Postgres e criar as tabelas com retry."""
    attempt = 1
    while True:
        try:
            print(f"[worker] Tentando conectar ao Postgres (tentativa {attempt})...")
            Base.metadata.create_all(bind=engine)
            print("[worker] Conectado ao Postgres e tabelas OK.")
            break
        except OperationalError as e:
            if attempt >= max_retries:
                print("[worker] Erro ao conectar ao Postgres, número máximo de tentativas atingido.")
                raise e
            print(f"[worker] Postgres ainda não está pronto, tentando de novo em {delay}s...")
            attempt += 1
            time.sleep(delay)


def create_consumer():
    conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": KAFKA_GROUP_ID,
        "auto.offset.reset": "earliest",
    }
    consumer = Consumer(conf)
    consumer.subscribe([KAFKA_CHAT_TOPIC])
    return consumer


def run_worker():
    consumer = create_consumer()
    print("[worker] Iniciado. Aguardando mensagens...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"[worker] Erro no Kafka: {msg.error()}")
                    continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                room_id = data["room_id"]
                sender_id = data["sender_id"]
                content = data["content"]

                db: Session = SessionLocal()
                try:
                    message = Message(
                        room_id=room_id,
                        sender_id=sender_id,
                        content=content,
                    )
                    db.add(message)
                    db.commit()
                    print(
                        f"[worker] Mensagem salva: room={room_id}, sender={sender_id}, content={content}"
                    )
                finally:
                    db.close()

            except Exception as e:
                print(f"[worker] Erro ao processar mensagem: {e}")

    except KeyboardInterrupt:
        print("[worker] Encerrando...")
    finally:
        consumer.close()


if __name__ == "__main__":
    # espera inicial opcional geral
    time.sleep(3)
    wait_for_db()
    run_worker()
