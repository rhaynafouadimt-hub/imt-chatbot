import redis
import json

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def save_message(session_id: str, role: str, content: str):
    key = f"chat:{session_id}"
    r.rpush(key, json.dumps({
        "role": role,
        "content": content
    }))


def load_history(session_id: str):
    key = f"chat:{session_id}"
    messages = r.lrange(key, 0, -1)
    return [json.loads(m) for m in messages]
