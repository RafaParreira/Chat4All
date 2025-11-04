from confluent_kafka import Producer
import json

conf = {'bootstrap.servers': 'kafka:9092'}
producer = Producer(conf)

def send_message(topic, message):
    producer.produce(topic, json.dumps(message).encode('utf-8'))
    producer.flush()