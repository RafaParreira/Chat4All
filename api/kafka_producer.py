from confluent_kafka import Producer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CHAT_TOPIC
import json
from typing import Dict

producer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
}

producer = Producer(producer_conf)


def delivery_report(err, msg):
    if err is not None:
        # aqui você pode logar de forma mais robusta depois
        print(f"Mensagem não entregue: {err}")
    else:
        print(
            f"Mensagem entregue em {msg.topic()} [partição {msg.partition()}], offset {msg.offset()}"
        )


def send_message_to_kafka(payload: Dict):
    data = json.dumps(payload).encode("utf-8")
    producer.produce(
        topic=KAFKA_CHAT_TOPIC,
        value=data,
        callback=delivery_report,
    )
    producer.poll(0)  # força envio assíncrono
