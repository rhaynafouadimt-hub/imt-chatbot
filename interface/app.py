import chainlit as cl
from ui.messages import WELCOME_MESSAGE

@cl.on_chat_start
async def start():
    await cl.Message(content=WELCOME_MESSAGE).send()

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content

    # ⚠️ TEMPORAIRE : plus tard ce sera l’agent NLP
    response = f"🧠 Question reçue : {user_input}"

    await cl.Message(content=response).send()
