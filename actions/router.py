from intent_classifier import detect_intent
from actions.email_action import generate_and_send_email
from actions.form_action import submit_contact_form
from confirmation import ask_confirmation


def route_message(
    llm,
    message: str,
    user_data: dict | None = None,
    session_state: dict | None = None
) -> str:
    """
    Route un message utilisateur selon son intention,
    avec confirmation obligatoire pour les actions.
    """

    if session_state is None:
        session_state = {}
    
    # Ignore les réponses oui/non hors confirmation
    if message.lower() in ["oui", "non", "yes", "no"] and not session_state.get("pending_intent"):
        return "Pouvez-vous préciser votre demande ?"

    # -----------------------
    # Confirmation
    # -----------------------
    if session_state.get("pending_intent"):
        if message.lower() in ["oui", "yes"]:
            intent = session_state["pending_intent"]
            session_state.clear()
        elif message.lower() in ["non", "no"]:
            session_state.clear()
            return "Action annulée. N’hésitez pas si vous avez une autre demande."
        else:
            return "Merci de répondre par *oui* ou *non*."
    else:
        intent = detect_intent(llm, message)
        if intent in ["ACTION_EMAIL", "ACTION_FORM"]:
            session_state["pending_intent"] = intent
            return ask_confirmation(intent)

    # -----------------------
    # ACTION : EMAIL
    # -----------------------
    if intent == "ACTION_EMAIL":
        success = generate_and_send_email(
            llm=llm,
            objet="Demande d'information – IMT",
            message=message
        )

        return (
            "L’email a été envoyé avec succès au Directeur de l’IMT."
            "N'hésitez pas si vous avez d'autres requettes."
            if success
            else "Désolé, une erreur est survenue lors de l’envoi de l’email."
        )

    # -----------------------
    # ACTION : FORMULAIRE
    # -----------------------
    if intent == "ACTION_FORM":
       return (
        #"Vous souhaitez contacter l’administration de l’IMT.\n\n"
        "Merci de remplir le formulaire officiel via le lien suivant :\n"
        "https://www.imt.sn/contact \n\n"
        "Pour des raisons de sécurité, le formulaire doit être rempli "
        "et validé manuellement."
        "N'hésitez pas si vous avez d'autres requettes."
       )

    # -----------------------
    # QUESTION (RAG)
    # -----------------------
    return "Cette demande sera traitée comme une question d’information. N'hésitez pas si vous avez d'autres requettes."
