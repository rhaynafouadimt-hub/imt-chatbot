"""
Package brain - Cœur intelligent du chatbot IMT.
Contient: LLM, orchestration, monitoring, configuration, prompts.
"""

from .config import config, initialize_config
from .llm import get_llm, get_langchain_llm, IMTLLM, LLMResponse
from .monitoring import get_monitor, LocalMonitor, TraceEvent, ActionType
from .prompts import (
    get_prompt, 
    get_chat_prompt, 
    SYSTEM_IDENTITY,
    format_conversation_history,
    get_time_based_greeting
)
from .utils import (
    clean_text,
    extract_json_from_text,
    retry_on_failure,
    timing_decorator,
    llm_api_decorator,
    serialize_for_redis,
    deserialize_from_redis,
    redis_key_builder
)

# À venir - sera ajouté quand chain.py sera créé
# from .chain import IMTConversationalChain, get_conversation_chain

__version__ = "1.0.0"
__author__ = "Équipe IMT Chatbot"
__description__ = "Cerveau du chatbot IMT avec LLM, LangChain et monitoring"

# Liste des exports publics
__all__ = [
    # Configuration
    "config",
    "initialize_config",
    
    # LLM
    "get_llm",
    "get_langchain_llm", 
    "IMTLLM",
    "LLMResponse",
    
    # Monitoring
    "get_monitor",
    "LocalMonitor",
    "TraceEvent",
    "ActionType",
    
    # Prompts
    "get_prompt",
    "get_chat_prompt",
    "SYSTEM_IDENTITY",
    "format_conversation_history",
    "get_time_based_greeting",
    
    # Utils
    "clean_text",
    "extract_json_from_text", 
    "retry_on_failure",
    "timing_decorator",
    "llm_api_decorator",
    "serialize_for_redis",
    "deserialize_from_redis",
    "redis_key_builder",
    
    # Version
    "__version__",
    "__author__",
    "__description__"
]

# Initialisation au chargement du package
def _initialize():
    """Initialisation automatique du package."""
    try:
        # Initialiser la configuration
        initialize_config()
        
        # Log de chargement
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🧠 Package brain v{__version__} chargé")
        logger.info(f"📋 Description: {__description__}")
        
    except Exception as e:
        import logging
        logging.error(f"❌ Erreur initialisation package brain: {e}")

# Exécuter l'initialisation
_initialize()