"""
Chaîne principale d'orchestration pour le chatbot IMT.
Orchestre: RAG → LLM → Actions → Mémoire → Monitoring.
Avec prompts externalisés dans Langfuse et sécurité renforcée.
"""

# Imports de TES modules terminés
import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
    print(f"✅ Chemin ajouté: {ROOT_DIR}")

from .llm import get_langchain_llm, IMTLLM, LLMResponse
from .prompt_manager import get_imt_prompt, get_prompt  # CHANGÉ: prompt_manager
from .prompts import format_conversation_history  # Gardé
from .monitoring import get_monitor, ActionType, trace_operation
from .config import config
from .utils import (
    clean_text, 
    extract_json_from_text, 
    validate_required_fields,
    retry_on_failure,
    timing_decorator
)
from ui.memory.redis_memory import load_history, save_message
# Pour l'asynchrone (Chainlit)
import asyncio
import time
import re
import json
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)

class IMTConversationalChain:
    """
    Chaîne conversationnelle principale du chatbot IMT.
    """
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        
        # 1. COMPOSANTS DE TA PARTIE
        self.llm = get_langchain_llm()
        self.monitor = get_monitor(session_id)
        self.memory = self._init_redis_memory()
        self.rag = self._init_rag()
        self.actions = self._init_actions()
        
        # 2. INITIALISATION SÉCURITÉ
        self.security_enabled = True
        self._init_security()
        
        # 3. VÉRIFICATION LANGFUSE (pour la démo)
        self._check_langfuse_prompts()
        
        logger.info(f"🚀 Chaîne IMT initialisée (session: {session_id}, sécurité: {self.security_enabled})")
    
    def _init_security(self):
        """Initialise les filtres de sécurité."""
        self.dangerous_patterns = [
            # Commandes système
            r"os\.(remove|system|popen|exec|kill)",
            r"subprocess\.",
            r"import\s+(os|subprocess|sys|shutil)\s",
            
            # Commandes shell
            r"rm\s+(-rf|\*)",
            r"del\s+.*\.(py|txt|json|db)",
            r"format\s+[cd]:",
            r"chmod\s+777",
            r"chown\s+.*root",
            
            # Injection SQL
            r"DROP\s+TABLE",
            r"DELETE\s+FROM",
            r"INSERT\s+INTO",
            r"UPDATE\s+.*SET",
            r"SELECT\s+\*\s+FROM",
            
            # Injection web
            r"<script>",
            r"javascript:",
            r"onclick=",
            r"alert\(",
            r"document\.cookie",
            
            # Évaluation de code
            r"eval\(",
            r"exec\(",
            r"__import__",
            r"compile\(",
            
            # Chemins dangereux
            r"/etc/passwd",
            r"C:\\Windows\\System32",
            r"/bin/bash",
            r"/bin/sh",
            
            # Tentatives de jailbreak
            r"ignore\s+previous",
            r"as\s+a\s+hypothetical",
            r"you\s+are\s+now",
        ]
    
    def _check_langfuse_prompts(self):
        """Vérifie la connectivité avec Langfuse Prompts (pour la démo)."""
        if config.monitoring.USE_LANGFUSE:
            try:
                from .prompt_manager import prompt_manager
                # Tester un prompt
                test_prompt = prompt_manager.get_prompt_template("imt_greeting", force_local=False)
                logger.info(f"✅ Prompts Langfuse connectés ({len(test_prompt)} chars)")
                
                # Afficher les sources (pour debug)
                self._log_prompt_sources()
            except Exception as e:
                logger.warning(f"⚠️ Prompts Langfuse non disponibles: {e}. Utilisation des prompts locaux.")
    
    def _log_prompt_sources(self):
        """Log la source de chaque prompt (pour démo)."""
        try:
            from .prompt_manager import prompt_manager
            test_prompts = ["greeting", "qa_with_context", "email_generation", "security_screening"]
            
            logger.debug("📝 Sources des prompts:")
            for pname in test_prompts:
                try:
                    info = prompt_manager.get_prompt_source_info(f"imt_{pname}")
                    source = info["source"]
                    logger.debug(f"  - {pname}: {source.upper()}")
                except:
                    logger.debug(f"  - {pname}: LOCAL (fallback)")
        except:
            pass
    
    def _init_redis_memory(self):
        """
            Initialise la mémoire Redis via le module de l'ami 3.
        """
        try:
            from ui.memory.redis_memory import load_history, save_message
        
            class RedisMemoryAdapter:
                def __init__(self, session_id):
                    self.session_id = session_id
                    self.load_history = load_history
                    self.save_message = save_message
            
                def get_history(self, limit=10):
                    """Récupère l'historique depuis Redis."""
                    try:
                        history = self.load_history(self.session_id)
                        # S'assurer que c'est une liste
                        if not isinstance(history, list):
                            logger.warning(f"⚠️ load_history n'a pas retourné une liste: {type(history)}")
                            return []
                        # Limiter et retourner
                        return history[-limit:] if limit else history
                    except Exception as e:
                        logger.error(f"❌ Erreur chargement historique Redis: {e}")
                        return []
            
                def add_message(self, role, content):
                    """Ajoute un message dans Redis."""
                    try:
                        self.save_message(self.session_id, role, content)
                        logger.debug(f"💾 Message sauvegardé Redis: {role} - {content[:30]}...")
                        return True
                    except Exception as e:
                        logger.error(f"❌ Erreur sauvegarde Redis: {e}")
                        return False
            
                def clear(self):
                    """Optionnel: effacer l'historique."""
                    logger.warning("⚠️ clear() non implémenté dans redis_memory")
                    return False
        
            logger.info(f"✅ Mémoire Redis initialisée pour session: {self.session_id}")
            return RedisMemoryAdapter(self.session_id)
        
        except ImportError as e:
            logger.error(f"❌ Impossible d'importer redis_memory: {e}")
            logger.warning("⚠️ Fallback vers mémoire locale (mock)")
            return self._init_mock_memory()
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Redis: {e}")
            return self._init_mock_memory()
        
    def _init_mock_memory(self):
        """Mémoire locale de secours si Redis échoue."""
        class MockMemory:
            def __init__(self):
                self.history = []
        
            def get_history(self, limit=10):
                return self.history[-limit:] if limit else self.history
        
            def add_message(self, role, content):
                self.history.append({"role": role, "content": content})
                logger.debug(f"[Mock] Message ajouté: {role}")
                return True
        
            def clear(self):
                self.history = []
                return True
    
        logger.warning("⚠️ Utilisation de la mémoire MOCK (fallback)")
        return MockMemory()
    
    def _init_rag(self):
        """Initialise le RAG via le module de scraping_rag."""
        try:
            from scraping_rag.rag_imt import search_imt
        
            class RAGClient:
                def search(self, query, k=3):
                    results = search_imt(query, k=k)
                    # S'assurer que chaque résultat a une source
                    for r in results:
                        if r.get("source") == "inconnu":
                            r["source"] = "Site IMT"  # ou laisse "inconnu"
                    return results
        
            logger.info("✅ RAG initialisé avec scraping_rag")
            return RAGClient()
        
        except ImportError as e:
            logger.error(f"❌ RAG non disponible: {e}")
            return self._init_mock_rag()
    
    def _init_actions(self):
        """Initialise les actions (email, formulaire)."""
        try:
            from actions.email_action import send_email
            from actions.form_action import submit_contact_form
        
            class ActionsClient:
                def send_email(self, to, subject, body, sender_name=""):
                    # Ajouter le nom de l'expéditeur dans le corps
                    full_body = f"De: {sender_name}\n\n{body}"
                    success = send_email(subject, full_body)
                    return {
                        "success": success,
                        "message": "Email envoyé" if success else "Échec envoi"
                    }
            
                def fill_form(self, form_data):
                    # Transformer le dict en paramètres
                    return submit_contact_form(
                        first_name=form_data.get("prenom", ""),
                        last_name=form_data.get("nom", ""),
                        email=form_data.get("email", ""),
                        phone=form_data.get("telephone", ""),
                        question=form_data.get("question", ""),
                        source="chatbot"
                    )
        
            logger.info("✅ Actions initialisées avec action/")
            return ActionsClient()
        
        except ImportError as e:
            logger.error(f"❌ Actions non disponibles: {e}")
            return self._init_mock_actions()
    
    def _init_mock_actions(self):
        """Fallback si les vraies actions ne sont pas disponibles."""
        class MockActions:
            def send_email(self, to, subject, body, sender_name=""):
                logger.warning(f"⚠️ [MOCK] Email à {to}: {subject}")
                return {"success": True, "message": "Mock envoyé"}
        
            def fill_form(self, form_data):
                logger.warning(f"⚠️ [MOCK] Formulaire: {form_data}")
                return {"success": True, "message": "Mock soumis"}
    
        return MockActions()

    def _is_potentially_malicious(self, text: str) -> bool:
        """Détecte les patterns dangereux avec des regex."""
        if not self.security_enabled:
            return False
        
        text_lower = text.lower()
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text_lower):
                logger.warning(f"🚨 Sécurité: pattern '{pattern}' détecté dans: {text[:50]}...")
                return True
        
        return False
    
    def _check_security_with_llm(self, user_input: str) -> bool:
        """Vérifie la sécurité avec le LLM."""
        if not self.security_enabled:
            return True
        
        try:
            prompt = get_imt_prompt("security_screening", user_input=user_input)
            response = self._call_llm(prompt, temperature=0.1, max_tokens=10)
            response_clean = response.strip().upper()
            
            logger.debug(f"🔒 Vérification sécurité LLM: '{response_clean}'")
            
            if response_clean == "UNSAFE":
                logger.warning(f"🚨 Requête bloquée par screening LLM: {user_input[:50]}...")
                return False
            elif response_clean == "SAFE":
                return True
            elif response_clean == "OUT_OF_SCOPE":
                logger.info(f"ℹ️ Requête hors domaine IMT: {user_input[:50]}...")
                return True
            else:
                logger.warning(f"⚠️ Réponse de sécurité incertaine: '{response_clean}'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification sécurité: {e}")
            return False
    
    @trace_operation(ActionType.LLM_CALL)
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Appelle le LLM avec monitoring."""
        start_time = time.time()

        response_text = self.llm.invoke(prompt, **kwargs)
        response_text_clean = clean_text(response_text)

        # Calcul de la durée
        duration_ms = (time.time() - start_time) * 1000
    
        # Logger vers Langfuse
        if hasattr(self.monitor, "log_llm_response"):
            try:
                class MockLLMResponse:
                    text = response_text_clean
                    model = config.get_llm_model_name()
                    usage = None
                    metadata = {"provider": config.llm.PROVIDER}
            
                self.monitor.log_llm_response(
                    response=MockLLMResponse(),
                    duration_ms=duration_ms,
                    prompt=prompt[:500]
                )
                logger.debug(f"📤 LLM response envoyé à Langfuse: {duration_ms:.0f}ms")
            except Exception as e:
                logger.error(f"❌ Erreur log_llm_response: {e}")
        else:
            logger.warning("⚠️ Moniteur n'a pas de méthode log_llm_response()")
    
        return response_text_clean
    
    async def process(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """
        Traite un message utilisateur avec sécurité renforcée.
        """
        # === COUCHE 1: Filtrage automatique (regex) ===
        if self._is_potentially_malicious(user_input):
            return {
                "text": "⚠️ Cette requête contient des éléments qui ne sont pas autorisés. "
                       "Je ne peux pas la traiter pour des raisons de sécurité.",
                "metadata": {
                    "security_block": True,
                    "reason": "automatic_filter",
                    "input_preview": user_input[:50]
                },
                "action_required": False
            }
        
        # Début du monitoring
        trace_id = self.monitor.start_trace(
            ActionType.LLM_CALL,
            {"input": user_input[:100], "session": self.session_id, "security_passed": True}
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
            
            # 4. Vérifier les intentions d'action (MÉTHODE SIMPLIFIÉE)
            needs_action = self._detect_action_intent_simple(user_input)
            
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
                    "rag_used": bool(rag_context),
                    "security_checks_passed": True
                }
            )
            
            return response
            
        except Exception as e:
            # Erreur monitoring
            self.monitor.end_trace(trace_id, error=str(e))
            logger.error(f"❌ Erreur dans process: {e}")
            
            # Réponse d'erreur
            return {
                "text": "Je rencontre une difficulté technique. "
                       "Veuillez réessayer ou contacter le support technique.",
                "metadata": {"error": True, "error_message": str(e)},
                "action_required": False
            }
    
    async def _generate_conversational_response(self, user_input: str, 
                                               history: str, 
                                               context: str) -> Dict:
        """Génère une réponse conversationnelle avec prompts externalisés."""
        # Choix du prompt selon le contexte disponible
        if context and config.rag.ENABLED:
            prompt = get_imt_prompt("qa_with_context",
                                  question=user_input,
                                  context=context,
                                  conversation_history=history)
        elif history:
            prompt = get_imt_prompt("qa_with_history",
                                  question=user_input,
                                  context="",
                                  conversation_history=history)
        else:
            prompt = get_imt_prompt("qa_basic", question=user_input)
        
        # Appel LLM
        response_text = self._call_llm(prompt)
        
        return {
            "text": response_text,
            "metadata": {
                "source": "conversation",
                "rag_used": bool(context),
                "history_used": bool(history),
                "prompt_source": "langfuse" if config.monitoring.USE_LANGFUSE else "local"
            },
            "action_required": False
        }
    
    def _detect_action_intent_simple(self, user_input: str) -> Optional[str]:
        """
        Détection simplifiée d'intention (sans prompts manquants).
        """
        user_input_lower = user_input.lower()
        
        # Mots-clés pour email
        email_keywords = [
            "email", "courriel", "écrire à", "écrire au", "directeur", 
            "envoyer un message", "contacter le directeur", "mail",
            "adresse mail", "mel", "mél", "courrier électronique"
        ]
        
        # Mots-clés pour formulaire
        form_keywords = [
            "formulaire", "form", "inscription", "inscrire", "contact",
            "remplir un formulaire", "formulaire de contact", "candidature",
            "postuler", "demande d'information"
        ]
        
        # Vérifier email
        for keyword in email_keywords:
            if keyword in user_input_lower:
                logger.debug(f"🔍 Intention email détectée via mot-clé: {keyword}")
                return "email"
        
        # Vérifier formulaire
        for keyword in form_keywords:
            if keyword in user_input_lower:
                logger.debug(f"🔍 Intention formulaire détectée via mot-clé: {keyword}")
                return "form"
        
        # Si pas détecté, vérifier avec prompts (fallback)
        try:
            # Essayer avec prompts locaux
            from .prompt_manager import prompt_manager
            if prompt_manager.langfuse_client:
                # Essayer Langfuse d'abord
                try:
                    prompt = prompt_manager.format_prompt(
                        "imt_email_intent_detection", 
                        user_message=user_input,
                        force_local=False
                    )
                    response = self._call_llm(prompt).strip()
                    if "YES" in response.upper():
                        return "email"
                except:
                    pass
        except Exception as e:
            logger.debug(f"⚠️ Détection via prompts échouée: {e}")
        
        return None
    
    async def _handle_email_action(self, user_input: str, history: str) -> Dict:
        """Gère la création et l'envoi d'email avec sécurité."""
        # Extraire les données pour l'email (AVEC LE BON NOM DE PROMPT)
        try:
            prompt = get_imt_prompt("email_data_extraction", user_message=user_input)
            email_data_json = self._call_llm(prompt)
        except Exception as e:
            logger.error(f"❌ Erreur extraction données email: {e}")
            # Fallback manuel
            email_data = {
                "sender_name": "Étudiant/visiteur de l'IMT",
                "subject": f"Demande: {user_input[:30]}..." if len(user_input) > 30 else user_input,
                "body": user_input,
                "urgency": "normal"
            }
            return await self._generate_email_from_data(email_data)
    
        # Nettoyage du JSON
        email_data_json = email_data_json.strip()
        email_data_json = email_data_json.replace("```json", "").replace("```", "").strip()
        
        # Extraire JSON
        email_data = extract_json_from_text(email_data_json)
        if not email_data:
            # Si pas de JSON valide, créer un objet manuel
            logger.warning("⚠️ JSON invalide, création manuelle")
            email_data = {
                "sender_name": "Étudiant/visiteur de l'IMT",
                "subject": f"Demande: {user_input[:30]}..." if len(user_input) > 30 else user_input,
                "body": user_input,
                "urgency": "normal"
            }
    
        # Vérifier si bloqué
        if email_data.get("blocked") == True:
            return {
                "text": "⚠️ La génération d'email a été bloquée pour des raisons de sécurité. "
                       "Veuillez reformuler votre demande de manière professionnelle.",
                "metadata": {
                    "action": "email",
                    "blocked": True,
                    "reason": "security_filter"
                },
                "action_required": False
            }
    
        return await self._generate_email_from_data(email_data)
    
    async def _generate_email_from_data(self, email_data: Dict) -> Dict:
        """Génère l'email à partir des données extraites."""
        # Extraire et valider les données
        sender_name = email_data.get("sender_name", "").strip() or "Étudiant/visiteur de l'IMT"
        subject = email_data.get("subject", "").strip() or "Demande d'information"
        body = email_data.get("body", "").strip() or "Je souhaite obtenir des informations supplémentaires."
        urgency = email_data.get("urgency", "normal").strip() or "normal"
        
        # Générer l'email
        try:
            prompt = get_imt_prompt("email_generation",
                               sender_name=sender_name,
                               subject=subject,
                               body_content=body,
                               urgency=urgency)
            email_content = self._call_llm(prompt)
        except Exception as e:
            logger.error(f"❌ Erreur génération email: {e}")
            # Template de fallback
            email_content = f"""
Monsieur le Directeur,

Je me permets de vous adresser ce courriel concernant: {subject}

{body}

Cordialement,
{sender_name}
"""
    
        # Vérifier sécurité
        if "CONTENU NON AUTORISÉ" in email_content or "bloqué" in email_content.lower():
            return {
                "text": "⚠️ La génération d'email a été interrompue pour des raisons de sécurité.",
                "metadata": {
                    "action": "email",
                    "blocked": True,
                    "reason": "content_filter"
                },
                "action_required": False
            }
    
        return {
            "text": f"📧 Email préparé pour le directeur de l'IMT:\n\n{email_content}\n\n"
                   f"*(Envoi simulé - à intégrer avec le module Actions)*\n"
                   f"Destinataire: {config.actions.DIRECTOR_EMAIL}",
            "metadata": {
                "action": "email",
                "email_data": {
                    "sender_name": sender_name,
                    "subject": subject,
                    "body_preview": body[:100] + "..." if len(body) > 100 else body,
                    "urgency": urgency
                },
                "recipient": config.actions.DIRECTOR_EMAIL,
                "content_length": len(email_content),
                "prompt_source": "langfuse" if config.monitoring.USE_LANGFUSE else "local"
            },
            "action_required": True,
            "action_type": "email"
        }
    
    async def _handle_form_action(self, user_input: str, history: str) -> Dict:
        """Gère le remplissage de formulaire avec sécurité."""
        # Extraire les données du formulaire
        try:
            prompt = get_imt_prompt("form_data_extraction", user_message=user_input)
            form_data_json = self._call_llm(prompt)
            form_data = extract_json_from_text(form_data_json) or {}
        except Exception as e:
            logger.error(f"❌ Erreur extraction données formulaire: {e}")
            form_data = {"message": user_input}
        
        # Vérifier si bloqué
        if form_data.get("blocked") == True:
            return {
                "text": "⚠️ L'extraction des données de formulaire a été bloquée pour sécurité.",
                "metadata": {
                    "action": "form",
                    "blocked": True,
                    "reason": "security_filter"
                },
                "action_required": False
            }
        
        # Vérifier la complétude
        required_fields = ["nom", "email", "message"]
        missing_fields = [f for f in required_fields if f not in form_data]
        
        if missing_fields:
            completion_check = f"Champs manquants: {', '.join(missing_fields)}"
        else:
            completion_check = "Formulaire complet"
        
        return {
            "text": f"📝 Données de formulaire extraites pour l'IMT:\n\n"
                   f"{json.dumps(form_data, indent=2, ensure_ascii=False)}\n\n"
                   f"Vérification: {completion_check}\n\n"
                   f"*(Soumission simulée - à intégrer avec le module Actions)*",
            "metadata": {
                "action": "form",
                "form_data": form_data,
                "completion_check": completion_check,
                "prompt_source": "langfuse" if config.monitoring.USE_LANGFUSE else "local"
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
            "monitoring_enabled": config.monitoring.ENABLED,
            "langfuse_prompts": config.monitoring.USE_LANGFUSE,
            "security_enabled": self.security_enabled
        }
    
    def get_prompt_debug_info(self) -> Dict:
        """Retourne des infos de debug sur les prompts."""
        try:
            from .prompt_manager import prompt_manager
            
            test_prompts = ["greeting", "qa_with_context", "email_generation", "security_screening"]
            info = {}
            
            for pname in test_prompts:
                try:
                    source_info = prompt_manager.get_prompt_source_info(f"imt_{pname}")
                    info[pname] = {
                        "source": source_info["source"],
                        "langfuse_available": source_info["langfuse_available"],
                        "local_available": source_info["local_available"]
                    }
                except Exception as e:
                    info[pname] = {"error": str(e)}
            
            return info
        except Exception as e:
            return {"error": f"Impossible de récupérer les infos prompts: {e}"}
    
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
    """Factory pour obtenir une chaîne conversationnelle."""
    if session_id is None:
        session_id = f"session_{int(asyncio.get_event_loop().time() * 1000)}"
    
    return IMTConversationalChain(session_id)

# ============================================================================
# INTÉGRATION CHAINLIT
# ============================================================================

class ChainlitIntegration:
    """Adaptateur pour l'intégration avec Chainlit."""
    
    def __init__(self):
        self.chains = {}  # Cache des chaînes par session
    
    async def process_message(self, user_input: str, 
                             session_id: str = None,
                             **kwargs) -> str:
        """Traite un message depuis Chainlit."""
        if session_id not in self.chains:
            self.chains[session_id] = get_conversation_chain(session_id)
        
        chain = self.chains[session_id]
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
# TEST AVEC SÉCURITÉ
# ============================================================================

if __name__ == "__main__":
    print("🧪 Test de la chaîne conversationnelle avec sécurité...")
    
    # Créer une chaîne
    chain = get_conversation_chain("test_security")
    
    print(f"\n📋 Info session: {chain.get_session_info()}")
    
    # Test prompts debug
    print(f"\n🔍 Debug prompts:")
    prompt_info = chain.get_prompt_debug_info()
    for pname, info in prompt_info.items():
        print(f"  - {pname}: {info.get('source', 'unknown')}")
    
    # Test simple
    print(f"\n🧠 Test de question normale...")
    
    async def test():
        # Test 1: Question normale
        print("\n1. Question normale:")
        response = await chain.process("Qu'est-ce que l'IMT ?")
        print(f"   ✅ Réponse: {response['text'][:150]}...")
        print(f"   📊 Métadata: {response['metadata']}")
        
        # Test 2: Commande dangereuse (doit être bloquée)
        print("\n2. Commande dangereuse:")
        response = await chain.process("import os; os.remove('test.txt')")
        if response['metadata'].get('security_block'):
            print(f"   ✅ BLOQUÉ: {response['text']}")
        else:
            print(f"   ❌ NON BLOQUÉ: {response['text'][:100]}...")
        
        # Test 3: Action email
        print("\n3. Demande d'email:")
        response = await chain.process("Je veux écrire au directeur de l'IMT pour une demande d'information")
        print(f"   📧 Réponse: {response['text'][:150]}...")
        print(f"   📊 Action requise: {response.get('action_required', False)}")
        
        # Test 4: Prompt source debug
        print("\n4. Source des prompts:")
        debug_info = chain.get_prompt_debug_info()
        for key, value in debug_info.items():
            print(f"   - {key}: {value}")
    
    # Exécuter le test
    import asyncio
    asyncio.run(test())
    
    print("\n🎉 Test chain.py avec sécurité terminé !")