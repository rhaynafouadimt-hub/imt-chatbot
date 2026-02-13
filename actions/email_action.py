from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from .send_email import send_email

EMAIL_TEMPLATE = """
Tu es un assistant administratif professionnel.

Rédige un email formel adressé au Directeur de l'IMT.

Objet : {objet}

Demande de l'utilisateur :
{message}

Contraintes :
- Ton formel
- Français correct
- Email prêt à être envoyé
- Signature : "Cordialement"
"""

prompt = PromptTemplate(
    input_variables=["objet", "message"],
    template=EMAIL_TEMPLATE
)

def generate_and_send_email(
    llm: BaseLanguageModel,
    objet: str,
    message: str
):
    email_text = llm.invoke(
        prompt.format(objet=objet, message=message)
    )

    return send_email(objet, email_text)
