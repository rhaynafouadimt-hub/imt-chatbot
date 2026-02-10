from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel

INTENT_PROMPT = """
Tu es un classificateur d’intentions.

À partir du message utilisateur, réponds UNIQUEMENT par l’un des mots suivants :

- QUESTION
- ACTION_EMAIL
- ACTION_FORM

Message utilisateur :
"{message}"

Réponse (un seul mot) :
"""

prompt = PromptTemplate(
    input_variables=["message"],
    template=INTENT_PROMPT
)

def detect_intent(llm, message: str) -> str:
    msg = message.lower().strip()

    # -----------------------
    # PRIORITÉ : QUESTIONS
    # -----------------------
    if any(q in msg for q in ["?", "quel", "quels", "quelle", "combien", "comment", "où", "quand"]):
        return "QUESTION"

    # -----------------------
    # ACTION EMAIL
    # -----------------------
    if any(k in msg for k in ["email", "mail", "envoyer", "envoie", "courriel"]):
        return "ACTION_EMAIL"

    # -----------------------
    # ACTION FORMULAIRE
    # -----------------------
    if any(k in msg for k in ["contacter", "contact", "administration", "formulaire"]):
        return "ACTION_FORM"

    # -----------------------
    # FALLBACK LLM
    # -----------------------
    response = llm.invoke(prompt.format(message=message)).strip().upper()

    if response in ["QUESTION", "ACTION_EMAIL", "ACTION_FORM"]:
        return response

    return "QUESTION"

