"""
Configuration centralisée pour le chatbot IMT.
Tous les paramètres, URLs, clés API sont gérés ici.
Utilise les variables d'environnement avec des valeurs par défaut.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from dataclasses import field
import logging

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# CLASSES DE CONFIGURATION
# ============================================================================

@dataclass
class LLMConfig:
    """Configuration des modèles de langage."""
    
    # Fournisseurs
    PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # ollama, gemini, grok, openrouter
    
    # Modèles par défaut par fournisseur
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GROK_MODEL: str = os.getenv("GROK_MODEL", "grok-beta")
    
    # Paramètres généraux
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    
    # URLs des APIs
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    GEMINI_API_BASE: str = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
    GROK_API_BASE: str = os.getenv("GROK_API_BASE", "https://api.x.ai/v1")
    
    # Clés API (NE JAMAIS COMMITER!)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GROK_API_KEY: Optional[str] = os.getenv("GROK_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")

@dataclass
class RAGConfig:
    """Configuration du système RAG."""
    
    # Activation
    ENABLED: bool = os.getenv("RAG_ENABLED", "true").lower() == "true"
    
    # Mode de fonctionnement
    MODE: str = os.getenv("RAG_MODE", "mock")  # mock, api, direct
    
    # URLs
    IMT_WEBSITE_URL: str = os.getenv("IMT_WEBSITE_URL", "https://www.imt.sn")
    RAG_API_URL: str = os.getenv("RAG_API_URL", "http://localhost:8000/api/rag")
    
    # Paramètres de recherche
    SEARCH_K_RESULTS: int = int(os.getenv("RAG_SEARCH_K", "4"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_THRESHOLD", "0.5"))
    
    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    USE_OLLAMA_EMBEDDINGS: bool = os.getenv("USE_OLLAMA_EMBEDDINGS", "false").lower() == "true"

@dataclass
class MemoryConfig:
    """Configuration de la mémoire."""
    
    # Backend
    BACKEND: str = os.getenv("MEMORY_BACKEND", "redis")  # redis, local
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PREFIX: str = os.getenv("REDIS_PREFIX", "imt_chatbot:")
    
    # Session
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT", "60"))
    MAX_HISTORY_LENGTH: int = int(os.getenv("MAX_HISTORY_LENGTH", "20"))

@dataclass
class MonitoringConfig:
    """Configuration du monitoring."""
    
    # Activation
    ENABLED: bool = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    
    # Langfuse (observabilité avancée)
    USE_LANGFUSE: bool = os.getenv("USE_LANGFUSE", "false").lower() == "true"
    LANGFUSE_SECRET_KEY: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_PUBLIC_KEY: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")

@dataclass
class ActionsConfig:
    """Configuration des actions (emails, formulaires)."""
    
    # Email
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USER: Optional[str] = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD: Optional[str] = os.getenv("EMAIL_PASSWORD")
    DIRECTOR_EMAIL: str = os.getenv("DIRECTOR_EMAIL", "directeur@imt.sn")
    
    # Formulaire
    CONTACT_FORM_URL: str = os.getenv("CONTACT_FORM_URL", "https://www.imt.sn/contact")
    FORM_SUBMIT_METHOD: str = os.getenv("FORM_METHOD", "POST")  # POST, GET

@dataclass
class UIAuthConfig:
    """Configuration de l'interface et authentification."""
    
    # Chainlit
    CHAINLIT_HOST: str = os.getenv("CHAINLIT_HOST", "0.0.0.0")
    CHAINLIT_PORT: int = int(os.getenv("CHAINLIT_PORT", "8000"))
    
    # Authentification (optionnel)
    REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
    ALLOWED_USERS: list = field(default_factory=list)

    def __post_init__(self):
        # Traitement après initialisation
        if isinstance(self.ALLOWED_USERS, str):
            self.ALLOWED_USERS = self.ALLOWED_USERS.split(",") if self.ALLOWED_USERS else []

# ============================================================================
# CONFIGURATION PRINCIPALE
# ============================================================================

class Config:
    """
    Configuration principale qui agrège toutes les sous-configurations.
    Singleton pour accès global.
    """
    
    # Initialisation des configurations
    llm = LLMConfig()
    rag = RAGConfig()
    memory = MemoryConfig()
    monitoring = MonitoringConfig()
    actions = ActionsConfig()
    ui = UIAuthConfig()
    
    # Paramètres généraux
    PROJECT_NAME: str = "IMT Chatbot Assistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, staging, production
    
    # Chemins
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    LOGS_DIR: str = os.path.join(BASE_DIR, "logs")
    EXPORTS_DIR: str = os.path.join(BASE_DIR, "exports")
    
    @classmethod
    def setup_directories(cls):
        """Crée les répertoires nécessaires."""
        directories = [cls.DATA_DIR, cls.LOGS_DIR, cls.EXPORTS_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"📁 Répertoire créé/vérifié: {directory}")
    
    @classmethod
    def validate(cls) -> Dict[str, bool]:
        """
        Valide la configuration.
        Retourne un dict avec les validations.
        """
        validations = {
            "directories": True,
            "llm_provider": True,
            "redis_connection": True,
        }
        
        # Vérifier les répertoires
        try:
            cls.setup_directories()
        except Exception as e:
            logger.error(f"❌ Erreur création répertoires: {e}")
            validations["directories"] = False
        
        # Vérifier le provider LLM
        if cls.llm.PROVIDER not in ["ollama", "gemini", "grok", "openrouter"]:
            logger.warning(f"⚠️ Provider LLM inconnu: {cls.llm.PROVIDER}")
            validations["llm_provider"] = False
        
        # Vérifier Redis si utilisé
        if cls.memory.BACKEND == "redis":
            try:
                import redis
                redis_client = redis.Redis.from_url(cls.memory.REDIS_URL, socket_timeout=2)
                redis_client.ping()
                logger.info("✅ Connexion Redis OK")
            except Exception as e:
                logger.warning(f"⚠️ Redis non disponible: {e}")
                validations["redis_connection"] = False
        
        return validations
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convertit la configuration en dict (sans les secrets)."""
        config_dict = {
            "project": cls.PROJECT_NAME,
            "version": cls.VERSION,
            "environment": cls.ENVIRONMENT,
            "debug": cls.DEBUG,
            "llm": {
                "provider": cls.llm.PROVIDER,
                "temperature": cls.llm.TEMPERATURE,
                "max_tokens": cls.llm.MAX_TOKENS
            },
            "rag": {
                "enabled": cls.rag.ENABLED,
                "mode": cls.rag.MODE,
                "website_url": cls.rag.IMT_WEBSITE_URL
            },
            "memory": {
                "backend": cls.memory.BACKEND,
                "session_timeout": cls.memory.SESSION_TIMEOUT_MINUTES
            },
            "monitoring": {
                "enabled": cls.monitoring.ENABLED,
                "use_langfuse": cls.monitoring.USE_LANGFUSE
            },
            "paths": {
                "base_dir": cls.BASE_DIR,
                "data_dir": cls.DATA_DIR,
                "logs_dir": cls.LOGS_DIR
            }
        }
        
        # Ajouter les modèles spécifiques
        if cls.llm.PROVIDER == "ollama":
            config_dict["llm"]["model"] = cls.llm.OLLAMA_MODEL
        elif cls.llm.PROVIDER == "gemini":
            config_dict["llm"]["model"] = cls.llm.GEMINI_MODEL
        elif cls.llm.PROVIDER == "grok":
            config_dict["llm"]["model"] = cls.llm.GROK_MODEL
        
        return config_dict
    
    @classmethod
    def get_llm_model_name(cls) -> str:
        """Retourne le nom du modèle selon le provider."""
        provider_models = {
            "ollama": cls.llm.OLLAMA_MODEL,
            "gemini": cls.llm.GEMINI_MODEL,
            "grok": cls.llm.GROK_MODEL
        }
        return provider_models.get(cls.llm.PROVIDER, cls.llm.OLLAMA_MODEL)

# Instance unique
config = Config()

# ============================================================================
# INITIALISATION
# ============================================================================

def initialize_config():
    """Initialise et valide la configuration au démarrage."""
    logger.info(f"🚀 Initialisation configuration: {config.PROJECT_NAME} v{config.VERSION}")
    
    # Créer les répertoires
    config.setup_directories()
    
    # Configurer le logging
    setup_logging()
    
    # Valider
    validations = config.validate()
    
    # Log de la configuration (sans secrets)
    logger.info("📋 Configuration chargée:")
    safe_config = config.to_dict()
    for section, values in safe_config.items():
        if isinstance(values, dict):
            logger.info(f"  {section}:")
            for key, value in values.items():
                logger.info(f"    {key}: {value}")
        else:
            logger.info(f"  {section}: {values}")
    
    return all(validations.values())

def setup_logging():
    """Configure le système de logging."""
    log_level = getattr(logging, config.monitoring.LOG_LEVEL.upper(), logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Handler fichier si configuré
    handlers = [console_handler]
    
    if config.monitoring.LOG_FILE:
        log_file_path = os.path.join(config.LOGS_DIR, config.monitoring.LOG_FILE)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configurer le root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers
    )
    
    logger.info(f"📝 Logging configuré (niveau: {config.monitoring.LOG_LEVEL})")

# Initialiser au chargement du module
if os.getenv("SKIP_CONFIG_INIT", "false").lower() != "true":
    initialize_config()

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("⚙️ Test de la configuration...")
    
    # Afficher la configuration
    print(f"\n📋 Configuration IMT Chatbot:")
    print(f"  Projet: {config.PROJECT_NAME} v{config.VERSION}")
    print(f"  Environnement: {config.ENVIRONMENT}")
    print(f"  Debug: {config.DEBUG}")
    
    print(f"\n🤖 LLM:")
    print(f"  Provider: {config.llm.PROVIDER}")
    print(f"  Modèle: {config.get_llm_model_name()}")
    print(f"  Température: {config.llm.TEMPERATURE}")
    
    print(f"\n🔍 RAG:")
    print(f"  Activé: {config.rag.ENABLED}")
    print(f"  Mode: {config.rag.MODE}")
    print(f"  Site IMT: {config.rag.IMT_WEBSITE_URL}")
    
    print(f"\n🧠 Mémoire:")
    print(f"  Backend: {config.memory.BACKEND}")
    print(f"  Redis URL: {config.memory.REDIS_URL}")
    
    print(f"\n📊 Monitoring:")
    print(f"  Activé: {config.monitoring.ENABLED}")
    print(f"  Langfuse: {config.monitoring.USE_LANGFUSE}")
    
    # Validation
    print(f"\n✅ Validation configuration...")
    validations = config.validate()
    for check, status in validations.items():
        print(f"  {check}: {'✅' if status else '❌'}")
    
    print("\n✅ Test configuration terminé")