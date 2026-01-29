"""
Prompts pour le chatbot IMT.
Contient tous les templates de prompts utilisés par le système.
"""

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Dict, List, Optional

# Import de la configuration
from .config import config

# ============================================================================
# CONSTANTES ET PROMPTS SYSTÈME
# ============================================================================

SYSTEM_IDENTITY = f"""Tu es "IMT Assistant", l'assistant conversationnel intelligent de l'Institut Mines-Télécom (IMT) Sénégal.

TON IDENTITÉ:
- Tu es un assistant officiel de l'IMT Sénégal
- Site web: {config.rag.IMT_WEBSITE_URL}
- Contact: {config.actions.DIRECTOR_EMAIL}
- Tu es poli, professionnel et serviable
- Tu parles français courant avec une touche sénégalaise
- Tu es précis dans tes informations

TON RÔLE:
1. Répondre aux questions sur l'IMT (formations, admissions, frais, etc.)
2. Guider les utilisateurs dans leurs démarches
3. Proposer de l'aide pour les actions (emails, formulaires)
4. Maintenir une conversation naturelle et utile

TON COMPORTEMENT:
- Sois concis mais complet
- Vérifie tes informations avant de répondre
- Si tu ne sais pas, propose de chercher ou redirige vers le site
- Utilise un ton chaleureux mais professionnel
- Adapte ton langage à l'utilisateur (étudiant, parent, professionnel)

IMPORTANT: Tu DOIS toujours mentionner que tu es l'assistant de l'IMT Sénégal.
"""

# ============================================================================
# TEMPLATES DE BASE (PromptTemplate)
# ============================================================================

PROMPTS = {
    # --------------------------------------------------------------------
    # PROMPTS DE SALUTATION ET CONVERSATION
    # --------------------------------------------------------------------
    "greeting": PromptTemplate(
        input_variables=["user_name", "time_of_day"],
        template="""{time_of_day} {user_name} ! 👋

Je suis IMT Assistant, votre guide pour toutes les questions concernant l'Institut Mines-Télécom du Sénégal.

Je peux vous aider avec:
• Les formations et programmes d'études
• Les conditions d'admission et inscriptions
• Les frais de scolarité et bourses
• Les contacts et localisation
• Et bien plus encore!

Comment puis-je vous assister aujourd'hui?"""
    ),
    
    "greeting_no_name": PromptTemplate(
        input_variables=["time_of_day"],
        template="""{time_of_day} ! 👋

Je suis IMT Assistant, votre guide pour toutes les questions concernant l'Institut Mines-Télécom du Sénégal.

Je peux vous aider avec:
• Les formations et programmes d'études
• Les conditions d'admission et inscriptions
• Les frais de scolarité et bourses
• Les contacts et localisation
• Et bien plus encore!

Comment puis-je vous assister aujourd'hui?"""
    ),
    
    # --------------------------------------------------------------------
    # PROMPTS DE QUESTION-RÉPONSE (RAG)
    # --------------------------------------------------------------------
    "qa_basic": PromptTemplate(
        input_variables=["question"],
        template=f"""{SYSTEM_IDENTITY}

QUESTION DE L'UTILISATEUR: {{question}}

RÉPONSE (en français, maximum 3 paragraphes):"""
    ),
    
    "qa_with_context": PromptTemplate(
        input_variables=["question", "context"],
        template=f"""{SYSTEM_IDENTITY}

INFORMATIONS DISPONIBLES SUR L'IMT:
{{context}}

QUESTION DE L'UTILISATEUR: {{question}}

BASÉ SUR LE CONTEXTE CI-DESSUS, réponds en français.
Si l'information n'est pas dans le contexte, dis-le clairement et propose de consulter le site {config.rag.IMT_WEBSITE_URL}.

RÉPONSE (précise, basée sur les faits):"""
    ),
    
    "qa_with_history": PromptTemplate(
        input_variables=["question", "context", "conversation_history"],
        template=f"""{SYSTEM_IDENTITY}

HISTORIQUE DE LA CONVERSATION:
{{conversation_history}}

CONTEXTE EXTRACT DU SITE IMT:
{{context}}

NOUVELLE QUESTION: {{question}}

Instructions:
1. Tiens compte de l'historique pour éviter les répétitions
2. Utilise le contexte quand c'est pertinent
3. Sois cohérent avec tes réponses précédentes
4. Si la question nécessite une action (email, formulaire), propose ton aide

RÉPONSE:"""
    ),
    
    # --------------------------------------------------------------------
    # PROMPTS DE RECHERCHE ET EXTRACTION
    # --------------------------------------------------------------------
    "search_query_generator": PromptTemplate(
        input_variables=["question"],
        template="""À partir de cette question utilisateur, génère 3 requêtes de recherche courtes pour trouver des informations pertinentes sur le site de l'IMT.

Question: {question}

Génère UNIQUEMENT les 3 requêtes, une par ligne, sans numérotation.

Exemple:
formations en informatique
frais de scolarité master
admission licence"""
    ),
    
    "information_extractor": PromptTemplate(
        input_variables=["text", "topic"],
        template="""Extrait toutes les informations pertinentes sur "{topic}" à partir du texte suivant.

TEXTE:
{text}

Extrait les informations au format:
- [Point clé]: [Valeur ou description]

Exemple:
- Durée de la formation: 2 ans
- Frais de scolarité: 500 000 FCFA par an
- Prérequis: Baccalauréat scientifique"""
    ),
    
    "rag_query_optimizer": PromptTemplate(
        input_variables=["original_query", "conversation_context"],
        template="""Optimise cette requête de recherche pour le système RAG de l'IMT.

Requête originale: {original_query}
Contexte conversationnel: {conversation_context}

Génère 2 versions optimisées:
1. **Version précise:** Pour une recherche exacte sur le site IMT
2. **Version élargie:** Pour trouver des informations connexes

Format de réponse:
PRÉCISE: [requête optimisée]
ÉLARGIE: [requête élargie]"""
    ),
    
    "rag_result_evaluator": PromptTemplate(
        input_variables=["query", "search_results"],
        template="""Évalue la pertinence de ces résultats de recherche pour la requête.

Requête: {query}

Résultats trouvés:
{search_results}

Pour chaque résultat:
- Score de pertinence (0-10)
- Raison du score
- Informations clés à extraire

Retourne au format JSON."""
    ),
    
    # --------------------------------------------------------------------
    # PROMPTS D'ACTIONS (EMAILS)
    # --------------------------------------------------------------------
    "email_intent_detection": PromptTemplate(
        input_variables=["user_message"],
        template="""Analyse ce message utilisateur et détermine s'il veut envoyer un email au directeur de l'IMT.

Message: "{user_message}"

Réponds UNIQUEMENT par:
- "YES" si l'utilisateur veut envoyer un email/courrier
- "NO" sinon

Exemples:
"Je veux écrire au directeur" → "YES"
"Quels sont les frais?" → "NO"
"Comment contacter la direction?" → "YES" """
    ),
    
    "email_data_extraction": PromptTemplate(
        input_variables=["user_message"],
        template=f"""Extrait les informations nécessaires pour envoyer un email professionnel au directeur de l'IMT.

DESTINATAIRE FIXE: {config.actions.DIRECTOR_EMAIL} (Directeur de l'IMT Sénégal)

Message utilisateur: "{{user_message}}"

Extrait ces informations au format JSON:
{{
  "sender_name": "nom de l'expéditeur si mentionné",
  "subject": "sujet de l'email basé sur la demande",
  "body": "contenu détaillé de l'email basé sur la demande",
  "urgency": "normal/urgent si mentionné",
  "attachments_needed": "oui/non"
}}

Si une information n'est pas fournie, utilise une valeur par défaut appropriée.

JSON UNIQUEMENT:"""
    ),
    
    "email_generation": PromptTemplate(
        input_variables=["sender_name", "subject", "body_content", "urgency"],
        template=f"""Génère un email professionnel en français pour le Directeur de l'IMT Sénégal.

EXPÉDITEUR: {{sender_name}} (ou "Un étudiant/visiteur" si non spécifié)
SUJET: {{subject}}
CONTENU DEMANDÉ: {{body_content}}
URGENCE: {{urgency}}

Format d'email:
[Formule d'appel professionnelle]
[Introduction courte]
[Corps du message - développe le contenu demandé de manière structurée]
[Conclusion et formule de politesse]
[Signature avec coordonnées si disponibles]

Ton: Professionnel, respectueux, clair.
Longueur: 150-250 mots.

EMAIL GÉNÉRÉ:"""
    ),
    
    "email_confirmation": PromptTemplate(
        input_variables=["email_content"],
        template="""Voici l'email préparé pour le Directeur de l'IMT:

{email_content}

Voulez-vous:
1. Modifier l'email
2. Envoyer maintenant
3. Annuler

Répondez par 1, 2 ou 3."""
    ),
    
    # --------------------------------------------------------------------
    # PROMPTS D'ACTIONS (FORMULAIRES)
    # --------------------------------------------------------------------
    "form_intent_detection": PromptTemplate(
        input_variables=["user_message"],
        template="""Analyse ce message utilisateur et détermine s'il veut remplir le formulaire de contact de l'IMT.

Message: "{user_message}"

Réponds UNIQUEMENT par:
- "YES" si l'utilisateur veut remplir/soumettre un formulaire
- "NO" sinon

Exemples:
"Je veux m'inscrire" → "YES"
"Remplir le formulaire de contact" → "YES"
"Quelles sont les formations?" → "NO" """
    ),
    
    "form_data_extraction": PromptTemplate(
        input_variables=["user_message"],
        template=f"""Extrait les informations nécessaires pour remplir le formulaire de contact de l'IMT.

Champs du formulaire:
1. nom_complet (Nom et prénom)
2. email (Adresse email)
3. telephone (Numéro de téléphone)
4. sujet (Sujet du message)
5. message (Message détaillé)
6. formation_interesse (Formation qui intéresse)

Message utilisateur: "{{user_message}}"

Extrait les valeurs pour ces champs au format JSON. Si un champ n'est pas mentionné, laisse une chaîne vide.

JSON UNIQUEMENT:"""
    ),
    
    "form_completion_check": PromptTemplate(
        input_variables=["form_data"],
        template="""Vérifie si les données de formulaire sont complètes pour soumission.

Données: {form_data}

Champs obligatoires: nom_complet, email, sujet, message

Réponds au format:
COMPLÈTE: oui/non
CHAMPS MANQUANTS: liste des champs manquants
RECOMMANDATIONS: suggestions pour compléter

Exemple:
COMPLÈTE: non
CHAMPS MANQUANTS: email, message
RECOMMANDATIONS: Demander l'email de l'utilisateur et clarifier son message"""
    ),
    
    # --------------------------------------------------------------------
    # PROMPTS DE SUMMARIZATION ET SYNTHÈSE
    # --------------------------------------------------------------------
    "conversation_summary": PromptTemplate(
        input_variables=["conversation_history"],
        template="""Résume cette conversation avec l'utilisateur en 3-4 points clés.

CONVERSATION:
{conversation_history}

Résume:
1. Sujets principaux discutés
2. Informations fournies à l'utilisateur
3. Actions demandées ou proposées
4. Prochaines étapes si pertinent

Format: Liste à puces en français."""
    ),
    
    "session_continuity": PromptTemplate(
        input_variables=["previous_summary", "current_topic"],
        template="""Reprends la conversation précédente et adapte-la au nouveau sujet.

RÉSUMÉ DE LA SESSION PRÉCÉDENTE:
{previous_summary}

NOUVEAU SUJET ABORDÉ: {current_topic}

Génère une transition fluide qui:
1. Fait le lien avec la conversation précédente
2. Introduit le nouveau sujet
3. Garde le contexte utilisateur en mémoire

Transition (1-2 phrases):"""
    ),
    
    "memory_retrieval_prompt": PromptTemplate(
        input_variables=["session_id", "current_query"],
        template="""L'utilisateur (session: {session_id}) pose cette question: "{current_query}"

À partir de l'historique de cette session (si disponible), identifie:
1. Les informations déjà partagées avec l'utilisateur
2. Les préférences ou besoins exprimés précédemment
3. Le contexte de la conversation en cours

Si pertinent, référence l'historique dans ta réponse."""
    ),
    
    "information_synthesis": PromptTemplate(
        input_variables=["topic", "information_chunks"],
        template="""Synthesize ces informations sur "{topic}" en un texte cohérent.

INFORMATIONS:
{information_chunks}

Instructions:
- Élimine les redondances
- Organise de manière logique
- Garde les informations factuelles
- Utilise un langage clair et professionnel

SYNTHÈSE (en français):"""
    ),
    
    # --------------------------------------------------------------------
    # PROMPTS D'ERREUR ET FALLBACK
    # --------------------------------------------------------------------
    "error_fallback": PromptTemplate(
        input_variables=["error_type", "user_question"],
        template=f"""{SYSTEM_IDENTITY}

Je rencontre une difficulté technique ({{error_type}}) en traitant votre question.

Votre question: {{user_question}}

Veuillez:
1. Reformuler votre question plus simplement
2. Ou visiter directement notre site: {config.rag.IMT_WEBSITE_URL}
3. Ou nous contacter aux coordonnées officielles

Je m'excuse pour ce désagrément. Comment puis-je vous aider autrement?"""
    ),
    
    "out_of_context": PromptTemplate(
        input_variables=["user_question"],
        template=f"""{SYSTEM_IDENTITY}

Je suis spécialisé sur les questions concernant l'IMT Sénégal (formations, admissions, frais, etc.).

Votre question "{{user_question}}" semble hors de mon domaine d'expertise.

Je peux vous aider avec:
• Tout ce qui concerne l'IMT Sénégal
• Les démarches administratives liées à l'institut
• Les informations académiques

Pour d'autres sujets, je vous recommande de consulter les ressources appropriées.

Puis-je vous aider avec autre chose concernant l'IMT?"""
    ),
    
    # --------------------------------------------------------------------
    # PROMPTS DE NAVIGATION ET ORIENTATION
    # --------------------------------------------------------------------
    "navigation_guide": PromptTemplate(
        input_variables=["user_need"],
        template=f"""L'utilisateur a besoin d'aide pour: {{user_need}}

Sur le site {config.rag.IMT_WEBSITE_URL}, guide-le vers:
1. La section pertinente
2. Les pages spécifiques à consulter
3. Les documents à télécharger si disponibles
4. Les contacts appropriés

Sois précis avec les noms de sections et pages."""
    ),
    
    "next_steps": PromptTemplate(
        input_variables=["user_situation"],
        template="""Pour cette situation: {user_situation}

Propose les prochaines étapes concrètes:
1. [Étape immédiate]
2. [Étape à moyen terme]
3. [Documents à préparer]
4. [Délais à respecter]
5. [Contacts utiles]

Format: Liste numérotée avec détails pratiques."""
    ),
    
    # --------------------------------------------------------------------
    # PROMPTS POUR L'INTERFACE UTILISATEUR (CHAINLIT)
    # --------------------------------------------------------------------
    "ui_welcome_message": PromptTemplate(
        input_variables=["user_name"],
        template="""🎓 Bienvenue sur l'Assistant IMT, {user_name} !

Je suis votre assistant intelligent pour l'Institut Management et Technologie du Sénégal.

**Fonctionnalités disponibles:**
• 🔍 Recherche d'informations sur les formations
• 📧 Envoi d'emails au directeur
• 📝 Remplissage de formulaires
• 💬 Conversation naturelle en français

**Comment utiliser:**
1. Posez vos questions normalement
2. Pour un email, dites "Je veux écrire au directeur"
3. Pour un formulaire, dites "Je veux remplir le formulaire"

Prêt à commencer ? Posez votre première question !"""
    ),
    
    "ui_action_confirmation": PromptTemplate(
        input_variables=["action_type", "details"],
        template="""✅ Action confirmée !

Type: {action_type}
Détails: {details}

**Prochaines étapes:**
1. Vérifiez les informations ci-dessus
2. Cliquez sur "Confirmer" pour exécuter
3. Ou "Modifier" pour ajuster

Voulez-vous procéder ?"""
    ),
    
    "ui_error_message": PromptTemplate(
        input_variables=["error", "recovery_suggestion"],
        template="""⚠️ Désolé, une erreur est survenue

**Erreur:** {error}

**Solution suggérée:** {recovery_suggestion}

**Options:**
• Réessayer l'action
• Contacter le support technique
• Continuer avec une autre question

Que souhaitez-vous faire ?"""
    )
}

# ============================================================================
# CHAT PROMPTS (ChatPromptTemplate - pour les modèles de chat)
# ============================================================================

CHAT_PROMPTS = {
    "conversational": ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_IDENTITY),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessage(content="{input}")
    ]),
    
    "conversational_with_context": ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_IDENTITY),
        MessagesPlaceholder(variable_name="chat_history"),
        SystemMessage(content="Contexte IMT actuel: {context}"),
        HumanMessage(content="{input}")
    ]),
    
    "action_oriented": ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""{SYSTEM_IDENTITY}

Tu peux aussi aider les utilisateurs à:
1. Envoyer des emails au directeur ({config.actions.DIRECTOR_EMAIL})
2. Remplir des formulaires de contact
3. Trouver des informations spécifiques sur {config.rag.IMT_WEBSITE_URL}

Propose ton aide pour ces actions quand c'est pertinent."""),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessage(content="{input}")
    ])
}

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_prompt(prompt_name: str, **kwargs) -> str:
    """
    Retourne un prompt formaté.
    
    Args:
        prompt_name: Nom du prompt dans PROMPTS
        **kwargs: Variables à injecter dans le template
        
    Returns:
        str: Prompt formaté
        
    Raises:
        ValueError: Si le prompt n'existe pas
    """
    if prompt_name not in PROMPTS:
        raise ValueError(f"Prompt '{prompt_name}' non trouvé. Prompts disponibles: {list(PROMPTS.keys())}")
    
    return PROMPTS[prompt_name].format(**kwargs)


def get_chat_prompt(prompt_name: str, **kwargs) -> ChatPromptTemplate:
    """
    Retourne un ChatPromptTemplate.
    
    Args:
        prompt_name: Nom du prompt dans CHAT_PROMPTS
        **kwargs: Variables pour le template
        
    Returns:
        ChatPromptTemplate: Prompt de chat formaté
    """
    if prompt_name not in CHAT_PROMPTS:
        raise ValueError(f"Chat prompt '{prompt_name}' non trouvé. Disponibles: {list(CHAT_PROMPTS.keys())}")
    
    return CHAT_PROMPTS[prompt_name].partial(**kwargs)


def get_time_based_greeting() -> str:
    """
    Retourne une salutation basée sur l'heure.
    
    Returns:
        str: "Bonjour", "Bon après-midi", "Bonsoir", etc.
    """
    from datetime import datetime
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Bonjour"
    elif 12 <= hour < 18:
        return "Bon après-midi"
    else:
        return "Bonsoir"


def format_conversation_history(messages: List[Dict]) -> str:
    """
    Formate l'historique de conversation pour les prompts.
    
    Args:
        messages: Liste de messages au format {'role': 'user'|'assistant', 'content': '...'}
        
    Returns:
        str: Historique formaté
    """
    if not messages:
        return "Aucun historique de conversation."
    
    formatted = []
    for i, msg in enumerate(messages, 1):
        role = "UTILISATEUR" if msg.get("role") == "user" else "ASSISTANT IMT"
        content = msg.get("content", "")
        formatted.append(f"{i}. {role}: {content}")
    
    return "\n".join(formatted)


def get_dynamic_prompt(prompt_name: str, context_vars: Dict = None) -> PromptTemplate:
    """
    Retourne un prompt avec des variables dynamiques de la config.
    
    Args:
        prompt_name: Nom du prompt
        context_vars: Variables supplémentaires à injecter
        
    Returns:
        PromptTemplate: Prompt avec variables résolues
    """
    if prompt_name not in PROMPTS:
        raise ValueError(f"Prompt '{prompt_name}' non trouvé")
    
    prompt = PROMPTS[prompt_name]
    
    # Variables par défaut depuis la config
    default_vars = {
        "institute_name": PROMPT_CONFIG["institute_name"],
        "website_url": PROMPT_CONFIG["website"],
        "contact_email": PROMPT_CONFIG["contact_email"],
        "max_response_length": PROMPT_CONFIG["max_response_length"]
    }
    
    # Fusionner avec les variables fournies
    if context_vars:
        default_vars.update(context_vars)
    
    # Retourner une copie avec les variables partielles
    return prompt.partial(**default_vars)


def inject_config_into_prompt(prompt_text: str) -> str:
    """
    Injecte les valeurs de configuration dans un texte de prompt.
    
    Args:
        prompt_text: Texte du prompt avec placeholders
        
    Returns:
        str: Prompt avec valeurs injectées
    """
    replacements = {
        "{{institute_name}}": PROMPT_CONFIG["institute_name"],
        "{{website_url}}": PROMPT_CONFIG["website"],
        "{{contact_email}}": PROMPT_CONFIG["contact_email"],
        "{{contact_phone}}": PROMPT_CONFIG.get("contact_phone", "")
    }
    
    result = prompt_text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    
    return result


# ============================================================================
# CONSTANTES DE CONFIGURATION DES PROMPTS
# ============================================================================

PROMPT_CONFIG = {
    "max_response_length": 500,  # mots maximum
    "default_temperature": config.llm.TEMPERATURE,
    "include_sources": True,
    "language": "fr",
    "institute_name": "Institut Management et Technologie (IMT) Sénégal",
    "website": config.rag.IMT_WEBSITE_URL,
    "contact_email": config.actions.DIRECTOR_EMAIL,
    "contact_phone": "+221 XX XXX XX XX",
}


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "PROMPTS",
    "CHAT_PROMPTS",
    "SYSTEM_IDENTITY",
    "get_prompt",
    "get_chat_prompt",
    "get_time_based_greeting",
    "format_conversation_history",
    "get_dynamic_prompt",
    "inject_config_into_prompt",
    "PROMPT_CONFIG"
]

# Test rapide si exécuté directement
if __name__ == "__main__":
    print("✅ brain/prompts.py chargé avec succès!")
    print(f"📝 {len(PROMPTS)} prompts disponibles")
    print(f"💬 {len(CHAT_PROMPTS)} chat prompts disponibles")
    
    # Test d'un prompt
    test_prompt = get_prompt(
        "greeting",
        user_name="Marie",
        time_of_day=get_time_based_greeting()
    )
    print(f"\n📋 Exemple de prompt greeting:\n{test_prompt[:200]}...")