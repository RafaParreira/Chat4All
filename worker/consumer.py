import json
import time
import threading
import psutil

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    start_http_server,
)

from confluent_kafka import Consumer, KafkaError
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CHAT_TOPIC, KAFKA_GROUP_ID
from db import SessionLocal, engine, Base
from models import Message


# ============================
#   Métricas Prometheus Worker
# ============================
WORKER_MESSAGES_PROCESSED = Counter(
    "worker_messages_processed_total",
    "Total de mensagens processadas pelo worker",
)

WORKER_MESSAGES_ERRORS = Counter(
    "worker_messages_errors_total",
    "Total de erros ao processar mensagens no worker",
)

WORKER_MESSAGE_LATENCY = Histogram(
    "worker_message_latency_seconds",
    "Latência de processamento de cada mensagem em segundos",
)

WORKER_CPU_PERCENT = Gauge(
    "worker_cpu_percent",
    "Uso de CPU do worker em porcentagem",
)

WORKER_MEMORY_PERCENT = Gauge(
    "worker_memory_percent",
    "Uso de memória do worker em porcentagem",
)





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

            start_time = time.time()

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
                    WORKER_MESSAGES_PROCESSED.inc()
                finally:
                    db.close()

            except Exception as e:
                WORKER_MESSAGES_ERRORS.inc()
                print(f"[worker] Erro ao processar mensagem: {e}")

    finally:
                elapsed = time.time() - start_time
                WORKER_MESSAGE_LATENCY.observe(elapsed)


def start_metrics_server(port: int = 8004):
  
    # inicia servidor HTTP do Prometheus
    start_http_server(port)

    def _collect_usage():
        while True:
            WORKER_CPU_PERCENT.set(psutil.cpu_percent(interval=None))
            WORKER_MEMORY_PERCENT.set(psutil.virtual_memory().percent)
            time.sleep(5)

    t = threading.Thread(target=_collect_usage, daemon=True)
    t.start()

if __name__ == "__main__":
    # espera inicial opcional geral
    time.sleep(3)
    wait_for_db()
    start_metrics_server(port=8004)
    run_worker()
