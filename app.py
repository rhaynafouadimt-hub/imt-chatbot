import uuid
import chainlit as cl

from ui.components.starter_menu import get_starters
from ui.memory.redis_memory import save_message, load_history


#  DÉCLARATION OFFICIELLE DES STARTERS (OBLIGATOIRE)
@cl.set_starters
def starters():
    return get_starters()


@cl.on_chat_start
async def start():
    #  session_id persistant
    session_id = cl.user_session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        cl.user_session.set("session_id", session_id)

    #  Charger l'historique Redis
    history = load_history(session_id)

    if history:
        for msg in history:
            await cl.Message(
                content=msg["content"],
                author="IMT Bot" if msg["role"] == "assistant" else "User"
            ).send()
    #  PAS de set_starters ici (Chainlit s’en charge automatiquement)


@cl.on_message
async def main(message: cl.Message):
    session_id = cl.user_session.get("session_id")

    save_message(session_id, "user", message.content)

    response = f"Tu as dit : {message.content}"

    save_message(session_id, "assistant", response)

    await cl.Message(
        content=response,
        author="IMT Bot"
    ).send()
