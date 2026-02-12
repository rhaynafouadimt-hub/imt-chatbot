"""
Gestionnaire de prompts hybride : Langfuse + cache local.
Priorité à Langfuse si disponible, sinon fallback local.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from functools import lru_cache
import time
import json

from .config import config
from .prompts import PROMPTS, CHAT_PROMPTS, SYSTEM_IDENTITY
from .utils import timing_decorator, retry_on_failure, clean_text

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Manager unifié pour les prompts IMT.
    Utilise Langfuse comme source principale, avec fallback local intelligent.
    """
    
    def __init__(self, use_cache: bool = True, cache_ttl: int = 300):
        """
        Initialise le gestionnaire de prompts.
        
        Args:
            use_cache: Activer le cache mémoire pour les prompts
            cache_ttl: Durée de vie du cache en secondes
        """
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        
        # Sources
        self.local_prompts = PROMPTS
        self.local_chat_prompts = CHAT_PROMPTS
        
        # Caches
        self._prompt_cache: Dict[str, Dict] = {}
        self._last_fetch_time: Dict[str, float] = {}
        self._prompt_versions: Dict[str, int] = {}
        
        # Statistiques
        self.stats = {
            "langfuse_hits": 0,
            "local_fallbacks": 0,
            "cache_hits": 0,
            "total_requests": 0
        }
        
        # Client Langfuse
        self.langfuse_client = None
        self._init_langfuse()
        
        logger.info(f"📝 PromptManager initialisé (cache: {use_cache}, TTL: {cache_ttl}s)")
        logger.info(f"   Langfuse: {'✅' if self.langfuse_client else '❌'}")
        logger.info(f"   Prompts locaux: {len(self.local_prompts)}")
    
    def _init_langfuse(self):
        """Initialise le client Langfuse si configuré."""
        if not config.monitoring.USE_LANGFUSE:
            logger.debug("Langfuse désactivé dans la configuration")
            return
    
        try:
            # DEBUG: Vérifier que le module est trouvé
            import importlib.util
            spec = importlib.util.find_spec("langfuse")
            if spec is None:
                logger.error("❌ Module 'langfuse' introuvable par Python")
                return
        
            logger.debug(f"✅ Module langfuse trouvé à: {spec.origin}")
        
            from langfuse import Langfuse
        
            logger.info(f"🔗 Connexion à Langfuse: {config.monitoring.LANGFUSE_HOST}")
        
            # Créer le client avec timeout court
            self.langfuse_client = Langfuse(
                secret_key=config.monitoring.LANGFUSE_SECRET_KEY,
                public_key=config.monitoring.LANGFUSE_PUBLIC_KEY,
                host=config.monitoring.LANGFUSE_HOST,
                timeout=5,  # 5 secondes max
                            )
        
            # Tester avec une requête simple
            test_result = self._test_langfuse_connection()
            if test_result:
                logger.info("✅ Langfuse initialisé avec succès")
            else:
                logger.warning("⚠️ Langfuse: connexion OK mais erreur de test")
                # Garder le client quand même pour les prompts
            
        except ImportError as e:
            logger.error(f"❌ ImportError: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Langfuse: {e}")
            # Ne pas lever l'exception, on continue avec fallback local
    
    def _test_langfuse_connection(self) -> bool:
        """Teste la connexion à Langfuse."""
        if not self.langfuse_client:
            return False
        
        try:
            # Essayer de récupérer un prompt (même s'il n'existe pas)
            # pour tester la connexion
            self.langfuse_client.get_prompt("connection_test", version=999)
            logger.info("✅ Connexion Langfuse établie")
            return True
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                logger.debug("✅ Connexion Langfuse OK (même si prompt non trouvé)")
                return True
            else:
                logger.warning(f"⚠️ Connexion Langfuse problématique: {e}")
                return False
    
    def _is_cache_valid(self, prompt_name: str) -> bool:
        """Vérifie si un prompt en cache est encore valide."""
        if not self.use_cache:
            return False
        
        if prompt_name not in self._last_fetch_time:
            return False
        
        elapsed = time.time() - self._last_fetch_time[prompt_name]
        return elapsed < self.cache_ttl
    
    @retry_on_failure(max_attempts=2, delay=1.0, exceptions=(Exception,))
    def _fetch_from_langfuse(self, prompt_name: str) -> Optional[str]:
        """
        Récupère un prompt depuis Langfuse.
        
        Args:
            prompt_name: Nom du prompt dans Langfuse
            
        Returns:
            str: Template du prompt, ou None si non trouvé
        """
        if not self.langfuse_client:
            return None
        
        try:
            # Log pour debug
            logger.debug(f"🔍 Recherche prompt Langfuse: '{prompt_name}'")
            
            # Méthode 1: Essayer get_prompt (version stable)
            try:
                prompt = self.langfuse_client.get_prompt(prompt_name, version=1)
                
                if prompt and hasattr(prompt, 'prompt'):
                    # Version avec attribut 'prompt'
                    template = prompt.prompt
                    logger.debug(f"✅ Prompt '{prompt_name}' trouvé via get_prompt()")
                    return template
                elif prompt and hasattr(prompt, 'template'):
                    # Version avec attribut 'template'
                    template = prompt.template
                    logger.debug(f"✅ Prompt '{prompt_name}' trouvé via get_prompt().template")
                    return template
            except Exception as e1:
                logger.debug(f"⚠️ get_prompt() échoué pour '{prompt_name}': {e1}")
            
            # Méthode 2: Essayer avec labels
            try:
                # Chercher avec label IMT
                prompts = self.langfuse_client.fetch_prompts(labels=["imt"])
                for p in prompts:
                    if hasattr(p, 'name') and p.name == prompt_name:
                        template = getattr(p, 'prompt', getattr(p, 'template', None))
                        if template:
                            logger.debug(f"✅ Prompt '{prompt_name}' trouvé via labels")
                            return template
            except Exception as e2:
                logger.debug(f"⚠️ fetch_prompts() échoué: {e2}")
            
            # Méthode 3: Essayer avec version None (latest)
            try:
                prompt = self.langfuse_client.get_prompt(prompt_name)
                if prompt:
                    template = getattr(prompt, 'prompt', getattr(prompt, 'template', None))
                    if template:
                        logger.debug(f"✅ Prompt '{prompt_name}' trouvé (latest version)")
                        return template
            except Exception as e3:
                logger.debug(f"⚠️ get_prompt(latest) échoué: {e3}")
            
            logger.warning(f"Prompt '{prompt_name}' non trouvé dans Langfuse")
            return None
            
        except Exception as e:
            logger.warning(f"Erreur récupération prompt '{prompt_name}' depuis Langfuse: {e}")
            return None
    
    def get_prompt_template(self, prompt_name: str, force_local: bool = False) -> str:
        """
        Récupère le template d'un prompt.
        
        Args:
            prompt_name: Nom du prompt
            force_local: Forcer l'utilisation du prompt local
            
        Returns:
            str: Template du prompt
            
        Raises:
            ValueError: Si le prompt n'existe nulle part
        """
        self.stats["total_requests"] += 1
        
        # 1. Forcer local si demandé ou Langfuse désactivé
        if force_local or not config.monitoring.USE_LANGFUSE or not self.langfuse_client:
            logger.debug(f"📝 '{prompt_name}' → FORCE LOCAL")
            self.stats["local_fallbacks"] += 1
            return self._get_local_template(prompt_name)
        
        # 2. Vérifier le cache
        if self.use_cache and self._is_cache_valid(prompt_name):
            logger.debug(f"📝 '{prompt_name}' → CACHE")
            self.stats["cache_hits"] += 1
            return self._prompt_cache[prompt_name]
        
        # 3. Essayer Langfuse
        logger.debug(f"📝 '{prompt_name}' → TENTATIVE LANGFUSE...")
        langfuse_template = self._fetch_from_langfuse(prompt_name)
        
        if langfuse_template:
            # Mettre en cache
            self._prompt_cache[prompt_name] = langfuse_template
            self._last_fetch_time[prompt_name] = time.time()
            self.stats["langfuse_hits"] += 1
            logger.info(f"✅ '{prompt_name}' → LANGFUSE ({len(langfuse_template)} chars)")
            return langfuse_template
        else:
            # Fallback local
            self.stats["local_fallbacks"] += 1
            logger.warning(f"⚠️ '{prompt_name}' → FALLBACK LOCAL (non trouvé dans Langfuse)")
            return self._get_local_template(prompt_name)
    
    def _get_local_template(self, prompt_name: str) -> str:
        """Récupère un template depuis la source locale."""
        if prompt_name not in self.local_prompts:
            # Essayer avec/sans préfixe imt_
            alt_name = prompt_name.replace("imt_", "") if prompt_name.startswith("imt_") else f"imt_{prompt_name}"
            
            if alt_name in self.local_prompts:
                logger.debug(f"  → Trouvé localement comme '{alt_name}'")
                return self.local_prompts[alt_name].template
            
            raise ValueError(
                f"Prompt '{prompt_name}' inconnu. "
                f"Prompts locaux: {list(self.local_prompts.keys())[:10]}..."
            )
        
        return self.local_prompts[prompt_name].template
    
    @timing_decorator
    def format_prompt(self, prompt_name: str, variables: Dict[str, Any] = None, **kwargs) -> str:
        """
        Récupère et formate un prompt avec des variables.
        
        Args:
            prompt_name: Nom du prompt
            variables: Variables à injecter
            **kwargs: Variables additionnelles
            
        Returns:
            str: Prompt formaté
        """
        variables = variables or {}
        variables.update(kwargs)
        
        # Récupérer le template
        template = self.get_prompt_template(prompt_name)
        
        try:
            # Formater le prompt
            formatted = template.format(**variables)
            logger.debug(f"📝 Prompt '{prompt_name}' formaté ({len(formatted)} chars)")
            return formatted
            
        except KeyError as e:
            logger.error(f"❌ Variable manquante dans prompt '{prompt_name}': {e}")
            logger.error(f"   Variables fournies: {list(variables.keys())}")
            logger.error(f"   Variables nécessaires: {self._extract_variables(template)}")
            raise
        except Exception as e:
            logger.error(f"❌ Erreur formatage prompt '{prompt_name}': {e}")
            # Retourner le template brut en cas d'erreur
            return template
    
    def _extract_variables(self, template: str) -> List[str]:
        """Extrait les variables d'un template."""
        import re
        variables = re.findall(r'\{(\w+)\}', template)
        return list(set(variables))  # Supprimer les doublons
    
    def get_chat_prompt(self, prompt_name: str, variables: Dict[str, Any] = None):
        """
        Récupère un ChatPromptTemplate.
        Note: Langfuse ne gère pas nativement les ChatPromptTemplate,
        donc on utilise toujours la version locale.
        
        Args:
            prompt_name: Nom du chat prompt
            variables: Variables à injecter
            
        Returns:
            ChatPromptTemplate: Prompt formaté
        """
        if prompt_name not in self.local_chat_prompts:
            raise ValueError(f"Chat prompt '{prompt_name}' inconnu. Disponibles: {list(self.local_chat_prompts.keys())}")
        
        variables = variables or {}
        return self.local_chat_prompts[prompt_name].partial(**variables)
    
    # ============================================================================
    # FONCTIONS SPÉCIFIQUES IMT
    # ============================================================================
    
    def get_imt_prompt(self, prompt_name: str, variables: Dict[str, Any] = None, **kwargs) -> str:
        """
        Récupère un prompt IMT - version corrigée.
        N'ajoute PAS de variables par défaut automatiquement.
        """
        # Fusionner seulement les variables fournies
        all_vars = {}
        if variables:
            all_vars.update(variables)
        all_vars.update(kwargs)
    
        # Noms à essayer dans l'ordre :
        names_to_try = []
    
        # 1. Avec préfixe imt_ (pour Langfuse)
        if not prompt_name.startswith("imt_"):
            names_to_try.append(f"imt_{prompt_name}")
    
        # 2. Le nom tel quel
        names_to_try.append(prompt_name)
    
        # 3. Pour compatibilité : certains prompts locaux n'ont pas de préfixe
        # mais dans Langfuse ils l'ont
        if prompt_name in ["greeting", "qa_with_context", "security_screening", 
                      "email_data_extraction", "email_generation", "form_data_extraction"]:
            names_to_try.append(prompt_name)  # Déjà ajouté, mais au cas où
    
        # Essayer chaque nom
        last_error = None
        for name in names_to_try:
            try:
                # Pour certains prompts, ajouter des variables IMT si nécessaires
                if name in ["imt_greeting", "imt_qa_with_context", "imt_qa_with_history"]:
                    # Ces prompts acceptent les variables IMT
                    prompt_vars = all_vars.copy()
                    prompt_vars.update({
                        "website_url": config.rag.IMT_WEBSITE_URL,
                        "contact_email": config.actions.DIRECTOR_EMAIL,
                    })
                    return self.format_prompt(name, prompt_vars)
                else:
                    # Pour les autres prompts, utiliser seulement les variables fournies
                    return self.format_prompt(name, all_vars)
                
            except KeyError as e:
                last_error = f"Variable manquante: {e}"
                logger.debug(f"Prompt '{name}' - erreur variable: {e}")
                continue
            except ValueError as e:
                last_error = f"Prompt non trouvé: {e}"
                logger.debug(f"Prompt '{name}' non trouvé")
                continue
            except Exception as e:
                last_error = str(e)
                logger.debug(f"Erreur avec prompt '{name}': {e}")
                continue
    
        # Si tout a échoué, fallback local avec message d'erreur
        logger.warning(f"⚠️ Tous les prompts ont échoué pour '{prompt_name}', fallback local")
        logger.debug(f"Dernière erreur: {last_error}")
    
        try:
            # Fallback: utiliser le prompt local
            return self.format_prompt(prompt_name, all_vars, force_local=True)
        except Exception as e:
            # Dernier recours: message d'erreur
            return f"[ERREUR PROMPT: '{prompt_name}' non disponible. Variables: {list(all_vars.keys())}]"
    
    # ============================================================================
    # SYNCHRONISATION ET ADMINISTRATION
    # ============================================================================
    
    def sync_prompts_to_langfuse(self, prompts_to_sync: List[str] = None, version: int = 1):
        """
        Synchronise les prompts locaux vers Langfuse.
        
        Args:
            prompts_to_sync: Liste des noms de prompts à synchroniser
            version: Version à assigner dans Langfuse
        """
        if not self.langfuse_client:
            logger.error("❌ Langfuse non disponible pour synchronisation")
            return
        
        if prompts_to_sync is None:
            # Synchroniser tous les prompts principaux
            prompts_to_sync = [
                "greeting", "qa_with_context", "security_screening",
                "email_generation", "form_data_extraction"
            ]
        
        synced = 0
        skipped = 0
        
        for prompt_name in prompts_to_sync:
            if prompt_name not in self.local_prompts:
                logger.warning(f"⚠️ Prompt '{prompt_name}' inconnu localement")
                skipped += 1
                continue
            
            try:
                # Récupérer le template local
                template = self.local_prompts[prompt_name].template
                
                # Nom dans Langfuse (avec préfixe imt_)
                langfuse_name = f"imt_{prompt_name}"
                
                # Créer/uploader dans Langfuse
                self.langfuse_client.create_prompt(
                    name=langfuse_name,
                    prompt=template,
                    labels=["imt", "synced"],
                    version=version,
                    config={
                        "model": "gpt-4",
                        "temperature": 0.2,
                        "max_tokens": 1024
                    }
                )
                
                logger.info(f"✅ '{prompt_name}' → '{langfuse_name}' (v{version})")
                synced += 1
                
                # Petite pause pour éviter les rate limits
                time.sleep(0.5)
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"ℹ️ '{prompt_name}' existe déjà dans Langfuse")
                    skipped += 1
                else:
                    logger.error(f"❌ Erreur sync '{prompt_name}': {e}")
                    skipped += 1
        
        logger.info(f"📤 Synchronisation terminée: {synced} créés, {skipped} ignorés/erreurs")
    
    def get_prompt_source_info(self, prompt_name: str) -> Dict[str, Any]:
        """
        Retourne des informations sur la source d'un prompt.
        
        Args:
            prompt_name: Nom du prompt
            
        Returns:
            Dict: Informations sur la source
        """
        source = "unknown"
        template = None
        langfuse_available = False
        
        # Vérifier Langfuse d'abord
        if self.langfuse_client and config.monitoring.USE_LANGFUSE:
            try:
                template = self._fetch_from_langfuse(prompt_name)
                if template:
                    source = "langfuse"
                    langfuse_available = True
            except:
                pass
        
        # Si pas dans Langfuse, vérifier local
        if not template:
            if prompt_name in self.local_prompts:
                source = "local"
                template = self.local_prompts[prompt_name].template
            else:
                # Essayer sans préfixe
                alt_name = prompt_name.replace("imt_", "") if prompt_name.startswith("imt_") else prompt_name
                if alt_name in self.local_prompts:
                    source = "local"
                    template = self.local_prompts[alt_name].template
        
        return {
            "name": prompt_name,
            "source": source,
            "langfuse_available": langfuse_available,
            "local_available": prompt_name in self.local_prompts or prompt_name.replace("imt_", "") in self.local_prompts,
            "template_preview": clean_text(template or "", max_length=100),
            "template_length": len(template) if template else 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques d'utilisation.
        
        Returns:
            Dict: Statistiques
        """
        return {
            **self.stats,
            "cache_size": len(self._prompt_cache),
            "cache_ttl": self.cache_ttl,
            "langfuse_enabled": bool(self.langfuse_client and config.monitoring.USE_LANGFUSE),
            "local_prompts_count": len(self.local_prompts)
        }
    
    def clear_cache(self):
        """Vide le cache des prompts."""
        self._prompt_cache.clear()
        self._last_fetch_time.clear()
        logger.info("🧹 Cache des prompts vidé")
    
    def list_available_prompts(self) -> Dict[str, List[str]]:
        """
        Liste tous les prompts disponibles.
        
        Returns:
            Dict: Prompts par source
        """
        return {
            "langfuse": self._list_langfuse_prompts(),
            "local": list(self.local_prompts.keys()),
            "chat_local": list(self.local_chat_prompts.keys())
        }
    
    def _list_langfuse_prompts(self) -> List[str]:
        """Liste les prompts disponibles dans Langfuse."""
        if not self.langfuse_client:
            return []
        
        try:
            prompts = self.langfuse_client.fetch_prompts()
            return [p.name for p in prompts if hasattr(p, 'name')]
        except:
            return []


# ============================================================================
# INSTANCE GLOBALE ET FONCTIONS D'ACCÈS
# ============================================================================

# Instance singleton
prompt_manager = PromptManager()

# Fonctions de compatibilité
def get_prompt(prompt_name: str, **kwargs) -> str:
    """
    Compatibilité avec l'ancienne fonction.
    
    Args:
        prompt_name: Nom du prompt
        **kwargs: Variables à injecter
        
    Returns:
        str: Prompt formaté
    """
    return prompt_manager.format_prompt(prompt_name, **kwargs)


def get_chat_prompt(prompt_name: str, **kwargs):
    """
    Compatibilité avec l'ancienne fonction.
    
    Args:
        prompt_name: Nom du chat prompt
        **kwargs: Variables à injecter
        
    Returns:
        ChatPromptTemplate: Prompt formaté
    """
    return prompt_manager.get_chat_prompt(prompt_name, kwargs)


def get_imt_prompt(prompt_name: str, **kwargs) -> str:
    """
    Fonction utilitaire pour les prompts IMT.
    
    Args:
        prompt_name: Nom du prompt (avec ou sans 'imt_')
        **kwargs: Variables à injecter
        
    Returns:
        str: Prompt formaté
    """
    return prompt_manager.get_imt_prompt(prompt_name, **kwargs)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("🧪 TEST DU PROMPT MANAGER AVEC LANGFUSE")
    print("=" * 60)
    
    # Configuration
    print(f"\n⚙️ CONFIGURATION:")
    print(f"  USE_LANGFUSE: {config.monitoring.USE_LANGFUSE}")
    print(f"  LANGFUSE_HOST: {config.monitoring.LANGFUSE_HOST}")
    print(f"  Client disponible: {'✅' if prompt_manager.langfuse_client else '❌'}")
    
    # Test prompts IMT
    print(f"\n🔍 TEST DES PROMPTS IMT:")
    
    test_cases = [
        ("imt_greeting", {"user_name": "Évaluateur", "time_of_day": "Bonjour"}),
        ("imt_security_screening", {"user_input": "import os; os.remove('test')"}),
        ("imt_security_screening", {"user_input": "Quels sont les frais de l'IMT?"}),
        ("greeting", {"user_name": "Test Local", "time_of_day": "Bonsoir"}),  # Local
    ]
    
    for prompt_name, variables in test_cases:
        print(f"\n📝 Prompt: {prompt_name}")
        print(f"   Variables: {variables}")
        
        try:
            # Info source
            source_info = prompt_manager.get_prompt_source_info(prompt_name)
            print(f"   📍 Source: {source_info['source'].upper()}")
            print(f"   🌐 Langfuse: {'✅' if source_info['langfuse_available'] else '❌'}")
            
            # Formatage
            if "imt_" in prompt_name:
                # Utiliser la fonction IMT
                prompt_text = get_imt_prompt(prompt_name.replace("imt_", ""), **variables)
            else:
                # Utiliser la fonction standard
                prompt_text = get_prompt(prompt_name, **variables)
            
            print(f"   ✅ Formaté ({len(prompt_text)} chars)")
            print(f"   📄 Preview: {clean_text(prompt_text, max_length=80)}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    # Statistiques
    print(f"\n📊 STATISTIQUES:")
    stats = prompt_manager.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Liste des prompts disponibles
    print(f"\n📋 PROMOTS DISPONIBLES:")
    available = prompt_manager.list_available_prompts()
    print(f"   Langfuse: {len(available['langfuse'])} prompts")
    for p in available['langfuse'][:5]:  # Afficher les 5 premiers
        print(f"     - {p}")
    if len(available['langfuse']) > 5:
        print(f"     ... et {len(available['langfuse']) - 5} autres")
    
    print(f"\n   Locaux: {len(available['local'])} prompts")
    
    print("\n" + "=" * 60)
    print("✅ Test PromptManager terminé")