import os
import json
from confluent_kafka import Producer

# Lê do ambiente ou usa padrão (compatível com seu docker-compose)
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

conf = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "linger.ms": 10,          # pequeno buffer para agrupar mensagens
    "acks": "1",              # confirmação do líder suficiente
}

producer = Producer(conf)


def delivery_report(err, msg):
    """Callback chamado quando a mensagem é entregue ou falha."""
    if err is not None:
        print(f"❌ Erro ao entregar mensagem: {err}")
    else:
        print(f"✅ Mensagem entregue ao tópico '{msg.topic()}' [partição {msg.partition()}] offset {msg.offset()}")


def send_message(topic: str, message: dict):
    """
    Envia mensagem JSON para o Kafka no tópico especificado.
    Bloqueia até a entrega (producer.flush()).
    """
    try:
        payload = json.dumps(message).encode("utf-8")
        producer.produce(topic, value=payload, callback=delivery_report)
        producer.poll(0)  # aciona callbacks de entrega
        producer.flush()  # força envio imediato (para uso síncrono, como no seu projeto)
    except Exception as e:
        print(f"⚠️ Falha ao enviar mensagem para o Kafka: {e}")
        raise
