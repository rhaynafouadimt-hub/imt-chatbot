import redis
import json

class RedisChatMemory:
    def __init__(self, session_id: str):
        self.session_id = f"chat:{session_id}"
        self.client = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

    def add_message(self, role: str, content: str):
        self.client.rpush(
            self.session_id,
            json.dumps({"role": role, "content": content})
        )

    def get_history(self):
        return [
            json.loads(m)
            for m in self.client.lrange(self.session_id, 0, -1)
        ]

    def clear(self):
        self.client.delete(self.session_id)
