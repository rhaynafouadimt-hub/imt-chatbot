import chainlit as cl


@cl.on_chat_start
async def start():
    await cl.Message(
        content=(
            "👋 **Bienvenue sur l’assistant IMT**\n\n"
            "Je suis là pour vous fournir des informations "
            "sur l’Institut des Métiers du Tertiaire."
        )
    ).send()
