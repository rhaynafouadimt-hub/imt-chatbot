"""
Chaîne principale d'orchestration pour le chatbot IMT.
Orchestre: RAG → LLM → Actions → Mémoire → Monitoring.
"""

# Imports de TES modules terminés
from .llm import get_langchain_llm, IMTLLM, LLMResponse
from .prompts import get_prompt, get_chat_prompt, format_conversation_history
from .monitoring import get_monitor, ActionType, trace_operation
from .config import config
from .utils import (
    clean_text, 
    extract_json_from_text, 
    validate_required_fields,
    retry_on_failure,
    timing_decorator
)

# Pour l'asynchrone (Chainlit)
import asyncio
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)

class IMTConversationalChain:
    """
    Chaîne conversationnelle principale du chatbot IMT.
    """
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        
        # 1. COMPOSANTS DE TA PARTIE (DÉJÀ DISPONIBLES)
        self.llm = get_langchain_llm()           # Ton LLM
        self.monitor = get_monitor(session_id)   # Ton monitoring
        self.memory = self._init_memory()        # Mock pour l'instant
        self.rag = self._init_rag()              # Mock pour l'instant
        self.actions = self._init_actions()      # Mock pour l'instant
        
        logger.info(f"🚀 Chaîne IMT initialisée (session: {session_id})")
    
    def _init_memory(self):
        """Initialise la mémoire (Redis - à intégrer depuis ami 1)."""
        # TODO: Remplacer par l'import de l'interface Redis de ton ami
        # from interface.memory_manager import RedisMemory
        # return RedisMemory(self.session_id)
        
        # Mock pour l'instant
        class MockMemory:
            def get_history(self, limit=10):
                return []
            def add_message(self, role, content):
                logger.debug(f"[Mock] Message ajouté: {role}: {content[:50]}...")
            def clear(self):
                pass
        
        return MockMemory()
    
    def _init_rag(self):
        """Initialise le RAG (scraping - à intégrer depuis ami 2)."""
        # TODO: Remplacer par l'import du RAG de l'autre équipe
        # from rag.rag_engine import RAGEngine
        # return RAGEngine()
        
        # Mock pour l'instant
        class MockRAG:
            def search(self, query, k=3):
                logger.debug(f"[Mock] RAG recherche: {query}")
                return [{"content": f"Info mock sur: {query}", "source": "mock"}]
        
        return MockRAG()
    
    def _init_actions(self):
        """Initialise les actions (email/form - à intégrer depuis ami 3)."""
        # TODO: Remplacer par l'import des actions
        # from actions.action_handler import ActionHandler
        # return ActionHandler()
        
        # Mock pour l'instant
        class MockActions:
            def send_email(self, to, subject, body):
                logger.debug(f"[Mock] Email envoyé à: {to}")
                return True
            def fill_form(self, form_data):
                logger.debug(f"[Mock] Formulaire rempli")
                return True
        
        return MockActions()
    
    @trace_operation(ActionType.LLM_CALL)
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Appelle le LLM avec monitoring."""
        response = self.llm.invoke(prompt, **kwargs)
        return clean_text(response)
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """
        Traite un message utilisateur (flux principal).
        
        Args:
            user_input: Message de l'utilisateur
            **kwargs: Paramètres supplémentaires
            
        Returns:
            Dict: Réponse structurée
        """
        # Début du monitoring
        trace_id = self.monitor.start_trace(
            ActionType.LLM_CALL,
            {"input": user_input[:100], "session": self.session_id}
        )
        
        try:
            # 1. Sauvegarder l'input en mémoire
            self.memory.add_message("user", user_input)
            
            # 2. Récupérer l'historique
            history = self.memory.get_history(limit=5)
            history_str = format_conversation_history(history)
            
            # 3. Recherche RAG
            rag_results = self.rag.search(user_input, k=config.rag.SEARCH_K_RESULTS)
            rag_context = "\n".join([r["content"] for r in rag_results[:3]])
            
            # 4. Vérifier les intentions d'action
            needs_action = self._detect_action_intent(user_input)
            
            # 5. Générer la réponse
            if needs_action == "email":
                response = await self._handle_email_action(user_input, history_str)
            elif needs_action == "form":
                response = await self._handle_form_action(user_input, history_str)
            else:
                # Réponse conversationnelle normale
                response = await self._generate_conversational_response(
                    user_input, history_str, rag_context
                )
            
            # 6. Sauvegarder la réponse en mémoire
            self.memory.add_message("assistant", response["text"])
            
            # 7. Fin du monitoring
            self.monitor.end_trace(
                trace_id,
                output_data={
                    "response_length": len(response["text"]),
                    "action_type": needs_action,
                    "rag_used": bool(rag_context)
                }
            )
            
            return response
            
        except Exception as e:
            # Erreur monitoring
            self.monitor.end_trace(trace_id, error=str(e))
            logger.error(f"❌ Erreur dans process: {e}")
            
            # Réponse d'erreur
            return {
                "text": get_prompt("error_fallback", 
                                  error_type="système",
                                  user_question=user_input),
                "metadata": {"error": True, "error_message": str(e)},
                "action_required": False
            }
    
    async def _generate_conversational_response(self, user_input: str, 
                                               history: str, 
                                               context: str) -> Dict:
        """Génère une réponse conversationnelle."""
        # Choix du prompt selon le contexte disponible
        if context and config.rag.ENABLED:
            prompt = get_prompt("qa_with_context",
                              question=user_input,
                              context=context,
                              conversation_history=history)
        elif history:
            prompt = get_prompt("qa_with_history",
                              question=user_input,
                              context="",
                              conversation_history=history)
        else:
            prompt = get_prompt("qa_basic", question=user_input)
        
        # Appel LLM
        response_text = self._call_llm(prompt)
        
        return {
            "text": response_text,
            "metadata": {
                "source": "conversation",
                "rag_used": bool(context),
                "history_used": bool(history)
            },
            "action_required": False
        }
    
    def _detect_action_intent(self, user_input: str) -> Optional[str]:
        """Détecte si l'utilisateur veut une action spécifique."""
        # Utiliser le LLM pour détecter l'intention
        prompt = get_prompt("email_intent_detection", user_message=user_input)
        email_intent = self._call_llm(prompt).strip()
        
        if "YES" in email_intent.upper():
            return "email"
        
        prompt = get_prompt("form_intent_detection", user_message=user_input)
        form_intent = self._call_llm(prompt).strip()
        
        if "YES" in form_intent.upper():
            return "form"
        
        return None
    
    async def _handle_email_action(self, user_input: str, history: str) -> Dict:
        """Gère la création et l'envoi d'email."""
        # Extraire les données pour l'email
        prompt = get_prompt("email_data_extraction", user_message=user_input)
        email_data_json = self._call_llm(prompt)

        # ----------------- Nettoyage du JSON -----------------
        email_data_json = email_data_json.strip()
        if email_data_json.startswith("```json"):
            email_data_json = email_data_json[7:]
        if email_data_json.endswith("```"):
            email_data_json = email_data_json[:-3]

        elif email_data_json.startswith("```"):
            email_data_json = email_data_json[3:]
            if email_data_json.endswith("```"):
                email_data_json = email_data_json[:-3]

        if email_data_json.lower().startswith("json"):
            email_data_json = email_data_json[4:].strip()

        email_data_json = email_data_json.strip('"\'')    
        # ------------------------------ Fin Nettoyage ------------------------

        email_data = extract_json_from_text(email_data_json) or {}
        
        # Générer l'email
        prompt = get_prompt("email_generation",
                           sender_name=email_data.get("sender_name", "Utilisateur"),
                           subject=email_data.get("subject", "Demande d'information"),
                           body_content=email_data.get("body", user_input),
                           urgency=email_data.get("urgency", "normal"))
        
        email_content = self._call_llm(prompt)
        
        # TODO: Envoyer l'email via l'interface d'actions
        # success = self.actions.send_email(
        #     to=config.actions.DIRECTOR_EMAIL,
        #     subject=email_data.get("subject"),
        #     body=email_content
        # )
        
        return {
            "text": f"📧 Email préparé pour le directeur:\n\n{email_content}\n\n*(Envoi mocké - à intégrer)*",
            "metadata": {
                "action": "email",
                "email_data": email_data,
                "recipient": config.actions.DIRECTOR_EMAIL
            },
            "action_required": True,
            "action_type": "email"
        }
    
    async def _handle_form_action(self, user_input: str, history: str) -> Dict:
        """Gère le remplissage de formulaire."""
        # Extraire les données du formulaire
        prompt = get_prompt("form_data_extraction", user_message=user_input)
        form_data_json = self._call_llm(prompt)
        form_data = extract_json_from_text(form_data_json) or {}
        
        # Vérifier la complétude
        prompt = get_prompt("form_completion_check", form_data=form_data)
        completion_check = self._call_llm(prompt)
        
        # TODO: Remplir le formulaire via l'interface d'actions
        # success = self.actions.fill_form(form_data)
        
        return {
            "text": f"📝 Données de formulaire extraites:\n\n{form_data}\n\nVérification: {completion_check}\n\n*(Soumission mockée - à intégrer)*",
            "metadata": {
                "action": "form",
                "form_data": form_data,
                "completion_check": completion_check
            },
            "action_required": True,
            "action_type": "form"
        }
    
    def get_session_info(self) -> Dict:
        """Retourne les informations de la session."""
        return {
            "session_id": self.session_id,
            "llm_provider": config.llm.PROVIDER,
            "model": config.get_llm_model_name(),
            "rag_enabled": config.rag.ENABLED,
            "monitoring_enabled": config.monitoring.ENABLED
        }
    
    def reset_session(self):
        """Réinitialise la session."""
        self.memory.clear()
        logger.info(f"🔄 Session réinitialisée: {self.session_id}")
        
        # Créer un nouveau moniteur
        self.monitor = get_monitor(self.session_id)

# ============================================================================
# FONCTIONS D'ACCÈS RAPIDE
# ============================================================================

def get_conversation_chain(session_id: str = None) -> IMTConversationalChain:
    """
    Factory pour obtenir une chaîne conversationnelle.
    
    Args:
        session_id: ID de session (optionnel)
        
    Returns:
        IMTConversationalChain: Instance de chaîne
    """
    if session_id is None:
        session_id = f"session_{int(asyncio.get_event_loop().time() * 1000)}"
    
    return IMTConversationalChain(session_id)

# ============================================================================
# INTÉGRATION CHAINLIT (pour ton ami)
# ============================================================================

class ChainlitIntegration:
    """
    Adaptateur pour l'intégration avec Chainlit.
    À utiliser par ton ami dans son interface.
    """
    
    def __init__(self):
        self.chains = {}  # Cache des chaînes par session
    
    async def process_message(self, user_input: str, 
                             session_id: str = None,
                             **kwargs) -> str:
        """
        Traite un message depuis Chainlit.
        
        Args:
            user_input: Message de l'utilisateur
            session_id: ID de session Chainlit
            **kwargs: Paramètres supplémentaires
            
        Returns:
            str: Réponse textuelle
        """
        # Obtenir ou créer la chaîne pour cette session
        if session_id not in self.chains:
            self.chains[session_id] = get_conversation_chain(session_id)
        
        chain = self.chains[session_id]
        
        # Traiter le message
        result = await chain.process(user_input, **kwargs)
        
        return result["text"]
    
    def get_session_chain(self, session_id: str) -> IMTConversationalChain:
        """Retourne la chaîne pour une session spécifique."""
        if session_id not in self.chains:
            self.chains[session_id] = get_conversation_chain(session_id)
        return self.chains[session_id]

# Instance globale pour Chainlit
chainlit_adapter = ChainlitIntegration()

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("🧪 Test de la chaîne conversationnelle...")
    
    # Créer une chaîne
    chain = get_conversation_chain("test_session")
    
    print(f"\n📋 Info session: {chain.get_session_info()}")
    
    # Test simple
    print(f"\n🧠 Test de question...")
    
    async def test():
        response = await chain.process("Qu'est-ce que l'IMT ?")
        print(f"✅ Réponse: {response['text'][:200]}...")
        
        # Test d'action email
        print(f"\n📧 Test d'action email...")
        response = await chain.process("Je veux écrire au directeur pour une demande")
        print(f"✅ Réponse email: {response['text'][:200]}...")
    
    # Exécuter le test
    import asyncio
    asyncio.run(test())
    
    print("\n🎉 Test chain.py terminé !")