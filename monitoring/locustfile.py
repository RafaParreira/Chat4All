from locust import HttpUser, task, between
import random

class ChatUser(HttpUser):
    wait_time = between(0.05, 0.5)

    @task(5)
    def send_message(self):
        payload = {
            "room_id": 10,
            "sender_id": 1,
            "content": "Mensagem Locust " + str(random.randint(1, 1000000)),
        }
        self.client.post("/messages", json=payload, timeout=30)
