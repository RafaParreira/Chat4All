import json
import logging
import os
import threading
import time

from fastapi import FastAPI, Body
from pydantic import BaseModel
from confluent_kafka import Consumer, Producer, KafkaError

logging.basicConfig(level=logging.INFO)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

INSTAGRAM_OUTBOUND_TOPIC = os.getenv("INSTAGRAM_OUTBOUND_TOPIC", "instagram_outbound")
INSTAGRAM_INBOUND_TOPIC = os.getenv("INSTAGRAM_INBOUND_TOPIC", "instagram_inbound")

app = FastAPI(title="Chat4All - Instagram Connector Mock")


# ---------------------------
#   Kafka Producer helper
# ---------------------------
def get_producer() -> Producer:
    return Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})


# ---------------------------
#   Kafka Consumer loop
# ---------------------------
def _create_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "connector_instagram_mock",
            "auto.offset.reset": "earliest",
        }
    )


def consume_outbound_loop():
    consumer = _create_consumer()
    consumer.subscribe([INSTAGRAM_OUTBOUND_TOPIC])

    logging.info(
        "WhatsApp connector mock consumindo tópico: %s", INSTAGRAM_OUTBOUND_TOPIC 
    )

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logging.error("Erro no consumer Instagram: %s", msg.error())
                continue

            try:
                payload = json.loads(msg.value().decode("utf-8"))
            except Exception as e:
                logging.error("Falha ao decodificar mensagem: %s", e)
                continue

            user = payload.get("recipient_external_id") or payload.get("user_id")
            text = payload.get("content") or payload.get("text")

            logging.info("[Instagram] Enviando mensagem para usuário %s: %s", user, text)
            time.sleep(0.5)  # simular latência

            # Simula entrega
            logging.info("[Instagram] Entregue a usuário %s", user)

            # Aqui você poderia:
            # - publicar em outro tópico (ex.: whatsapp_status)
            # - ou futuramente fazer callback HTTP para a API central
    finally:
        consumer.close()


# ---------------------------
#   Modelos para inbound
# ---------------------------
class InstagramInboundMessage(BaseModel):
    external_user_id: str
    text: str


# ---------------------------
#   Endpoints FastAPI
# ---------------------------
@app.post("/mock/instagram/inbound")
def receive_inbound(msg: InstagramInboundMessage):
    producer = get_producer()
    event = {
        "channel": "instagram",
        "external_user_id": msg.external_user_id,
        "text": msg.text,
        "timestamp": int(time.time()),
    }
    producer.produce(
        INSTAGRAM_INBOUND_TOPIC,
        json.dumps(event).encode("utf-8"),
    )
    producer.flush()

    logging.info(
        "[Instagram][MOCK INBOUND] Mensagem recebida de %s: %s",
        msg.external_user_id,
        msg.text,
    )

    return {"status": "ok", "published_to": INSTAGRAM_INBOUND_TOPIC, "event": event}


# ---------------------------
#   Startup: iniciar consumer em thread
# ---------------------------
@app.on_event("startup")
def on_startup():
    t = threading.Thread(target=consume_outbound_loop, daemon=True)
    t.start()
    logging.info("Thread de consumo Instagram iniciada.")
