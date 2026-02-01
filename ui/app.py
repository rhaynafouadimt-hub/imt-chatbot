import chainlit as cl
from components.starter_menu import get_starters


@cl.set_starters
async def starters():
    return get_starters()


@cl.on_message
async def on_message(message: cl.Message):
    await cl.Message(
        content="🧠 Traitement en cours…"
    ).send()
