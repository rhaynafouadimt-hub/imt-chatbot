def ask_confirmation(intent: str) -> str:
    if intent == "ACTION_EMAIL":
        return (
            "Vous souhaitez que j’envoie un email formel "
            "au Directeur de l’IMT.\n"
            "Confirmez-vous l’envoi ? (oui / non)"
        )

    if intent == "ACTION_FORM":
        return (
            "Vous souhaitez contacter l’administration de l'IMT, je vais vous rediriger vers le formulaire.\n"
            "Confirmez-vous la requette ? (oui / non)"
        )

    return ""
