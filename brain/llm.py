"""
Module d'intégration LLM pour le chatbot IMT.
Support pour Gemini, Grok, et Ollama avec fallback.
"""
import warnings 
import os

# Suppression des warning google
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'
warnings.filterwarnings("ignore", category=FutureWarning)

import logging
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

# Import de la config et des utilitaires
from .config import config
from .utils import llm_api_decorator, retry_on_failure, extract_json_from_text, clean_text

# LangChain
from langchain_core.language_models.llms import BaseLLM
from langchain_core.outputs import LLMResult, Generation
from langchain_core.callbacks import CallbackManagerForLLMRun

logger = logging.getLogger(__name__)

# ============================================================================
# CLASSES ET TYPES
# ============================================================================

@dataclass
class LLMResponse:
    """Réponse structurée d'un LLM."""
    text: str
    raw_response: Any
    model: str
    usage: Optional[Dict] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convertit la réponse en dictionnaire."""
        return {
            "text": self.text,
            "model": self.model,
            "usage": self.usage,
            "metadata": self.metadata
        }

# ============================================================================
# FOURNISSEURS LLM
# ============================================================================

class GeminiProvider:
    """Provider pour Google Gemini."""
    
    def __init__(self):
        self.api_key = config.llm.GEMINI_API_KEY
        self.model_name = config.llm.GEMINI_MODEL
        self.base_url = config.llm.GEMINI_API_BASE
        
        if not self.api_key:
            raise ValueError("❌ Clé API Gemini manquante. Définissez GEMINI_API_KEY dans .env")
        
        # Importer conditionnellement
        try:
            import google.generativeai as genai
            self.genai = genai
            genai.configure(api_key=self.api_key)
        except ImportError:
            raise ImportError("Installez google-generativeai: pip install google-generativeai")
    
    @llm_api_decorator
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Génère une réponse avec Gemini.
        
        Args:
            prompt: Prompt à envoyer
            **kwargs: Paramètres supplémentaires
            
        Returns:
            LLMResponse: Réponse structurée
        """
        model = self.genai.GenerativeModel(self.model_name)
        
        # Paramètres de génération
        generation_config = {
            "temperature": kwargs.get("temperature", config.llm.TEMPERATURE),
            "max_output_tokens": kwargs.get("max_tokens", config.llm.MAX_TOKENS),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=self._get_safety_settings()
        )
        
        # Extraire le texte
        text = response.text if hasattr(response, 'text') else ""
        
        # Construire l'objet usage
        usage = None
        if hasattr(response, 'usage_metadata'):
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
            }
        
        return LLMResponse(
            text=clean_text(text),
            raw_response=response,
            model=self.model_name,
            usage=usage,
            metadata={"provider": "gemini"}
        )
    
    def _get_safety_settings(self):
        """Retourne les paramètres de sécurité pour Gemini."""
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]


class GrokProvider:
    """Provider pour xAI Grok."""
    
    def __init__(self):
        self.api_key = config.llm.GROK_API_KEY
        self.model_name = config.llm.GROK_MODEL
        self.base_url = config.llm.GROK_API_BASE
        
        if not self.api_key:
            raise ValueError("❌ Clé API Grok manquante. Définissez GROK_API_KEY dans .env")
        
        # Importer conditionnellement
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("Installez openai: pip install openai")
    
    @llm_api_decorator
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Génère une réponse avec Grok.
        
        Args:
            prompt: Prompt à envoyer
            **kwargs: Paramètres supplémentaires
            
        Returns:
            LLMResponse: Réponse structurée
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", config.llm.TEMPERATURE),
            max_tokens=kwargs.get("max_tokens", config.llm.MAX_TOKENS),
            top_p=kwargs.get("top_p", 0.9),
        )
        
        text = response.choices[0].message.content if response.choices else ""
        
        usage = None
        if hasattr(response, 'usage'):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        return LLMResponse(
            text=clean_text(text),
            raw_response=response,
            model=self.model_name,
            usage=usage,
            metadata={"provider": "grok"}
        )


class OllamaProvider:
    """Provider pour Ollama (local)."""
    
    def __init__(self):
        self.model_name = config.llm.OLLAMA_MODEL
        self.base_url = config.llm.OLLAMA_BASE_URL
        
        try:
            from langchain_community.llms import Ollama
            self.llm = Ollama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=config.llm.TEMPERATURE,
                num_predict=config.llm.MAX_TOKENS
            )
        except ImportError:
            raise ImportError("Installez langchain-community: pip install langchain-community")
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Génère une réponse avec Ollama.
        
        Args:
            prompt: Prompt à envoyer
            **kwargs: Paramètres supplémentaires
            
        Returns:
            LLMResponse: Réponse structurée
        """
        try:
            text = self.llm.invoke(prompt)
            
            return LLMResponse(
                text=clean_text(text),
                raw_response=text,
                model=self.model_name,
                metadata={"provider": "ollama"}
            )
        except Exception as e:
            logger.error(f"❌ Erreur Ollama: {e}")
            raise

# ============================================================================
# LLM UNIFIÉ (FACADE)
# ============================================================================

class IMTLLM:
    """
    LLM unifié pour le chatbot IMT.
    Gère automatiquement le provider configuré.
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialise le LLM avec le provider spécifié ou depuis la config.
        
        Args:
            provider: "gemini", "grok", "ollama" (optionnel)
        """
        self.provider_name = provider or config.llm.PROVIDER
        self._provider = None
        self._initialize_provider()
        
        logger.info(f"🚀 LLM initialisé: provider={self.provider_name}, model={self.model_name}")
    
    def _initialize_provider(self):
        """Initialise le provider approprié."""
        if self.provider_name == "gemini":
            self._provider = GeminiProvider()
        elif self.provider_name == "grok":
            self._provider = GrokProvider()
        elif self.provider_name == "ollama":
            self._provider = OllamaProvider()
        else:
            raise ValueError(f"Provider LLM non supporté: {self.provider_name}")
    
    @property
    def model_name(self) -> str:
        """Retourne le nom du modèle actuel."""
        return config.get_llm_model_name()
    
    @retry_on_failure(max_attempts=3, delay=1.0)
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Génère une réponse avec le LLM.
        
        Args:
            prompt: Prompt à envoyer
            **kwargs: Paramètres supplémentaires (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse: Réponse structurée
        """
        logger.debug(f"📤 Prompt ({len(prompt)} chars): {prompt[:100]}...")
        
        # Utiliser les paramètres par défaut de la config si non spécifiés
        temperature = kwargs.get("temperature", config.llm.TEMPERATURE)
        max_tokens = kwargs.get("max_tokens", config.llm.MAX_TOKENS)
        
        logger.info(f"⚡ Génération avec {self.provider_name} (temp={temperature}, max_tokens={max_tokens})")
        
        response = self._provider.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        logger.debug(f"📥 Réponse ({len(response.text)} chars): {response.text[:100]}...")
        return response
    
    def generate_json(self, prompt: str, **kwargs) -> Optional[Dict]:
        """
        Génère une réponse et tente de l'extraire comme JSON.
        
        Args:
            prompt: Prompt à envoyer
            **kwargs: Paramètres supplémentaires
            
        Returns:
            Optional[Dict]: Données JSON ou None
        """
        response = self.generate(prompt, **kwargs)
        return extract_json_from_text(response.text)
    
    def chat(self, messages: list, **kwargs) -> LLMResponse:
        """
        Génère une réponse à partir d'une conversation.
        
        Args:
            messages: Liste de messages [{"role": "user", "content": "..."}, ...]
            **kwargs: Paramètres supplémentaires
            
        Returns:
            LLMResponse: Réponse structurée
        """
        # Convertir les messages en prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role.capitalize()}: {content}")
        
        prompt = "\n\n".join(prompt_parts) + "\n\nAssistant: "
        return self.generate(prompt, **kwargs)

# ============================================================================
# ADAPTATEUR LANGCHAIN
# ============================================================================

class LangChainIMTLLM(BaseLLM):
    """
    Adaptateur LangChain pour IMTLLM.
    Permet d'utiliser IMTLLM dans les chaînes LangChain.
    """
    
    @property
    def _llm_type(self) -> str:
        return "imt_llm"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[list] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Appel principal pour LangChain.
        
        Args:
            prompt: Prompt à envoyer
            stop: Liste de tokens d'arrêt
            run_manager: Gestionnaire de callbacks
            **kwargs: Paramètres supplémentaires
            
        Returns:
            str: Réponse texte
        """
        llm = IMTLLM()
        response = llm.generate(prompt, **kwargs)
        return response.text
    
    def _generate(
        self,
        prompts: list[str],
        stop: Optional[list] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        Génération batch pour LangChain.
        
        Args:
            prompts: Liste de prompts
            stop: Tokens d'arrêt
            run_manager: Gestionnaire de callbacks
            **kwargs: Paramètres supplémentaires
            
        Returns:
            LLMResult: Résultat LangChain
        """
        generations = []
        llm = IMTLLM()
        
        for prompt in prompts:
            response = llm.generate(prompt, **kwargs)
            generations.append([Generation(text=response.text)])
        
        return LLMResult(generations=generations)
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Paramètres identifiants pour LangChain."""
        return {
            "provider": config.llm.PROVIDER,
            "model": config.get_llm_model_name(),
            "temperature": config.llm.TEMPERATURE,
            "max_tokens": config.llm.MAX_TOKENS
        }

# ============================================================================
# FONCTIONS D'ACCÈS RAPIDE
# ============================================================================

def get_llm() -> IMTLLM:
    """
    Retourne une instance de IMTLLM configurée.
    
    Returns:
        IMTLLM: Instance LLM
    """
    return IMTLLM()

def get_langchain_llm() -> LangChainIMTLLM:
    """
    Retourne un LLM compatible LangChain.
    
    Returns:
        LangChainIMTLLM: LLM pour LangChain
    """
    return LangChainIMTLLM()

def get_provider_info() -> Dict:
    """
    Retourne des informations sur le provider actuel.
    
    Returns:
        Dict: Informations du provider
    """
    return {
        "provider": config.llm.PROVIDER,
        "model": config.get_llm_model_name(),
        "available": bool(get_llm()._provider)
    }

# ============================================================================
# INITIALISATION ET TEST
# ============================================================================

def initialize_llm() -> IMTLLM:
    """
    Initialise et valide le LLM au démarrage.
    
    Returns:
        IMTLLM: Instance LLM initialisée
    """
    logger.info(f"🔧 Initialisation LLM: provider={config.llm.PROVIDER}")
    
    try:
        llm = IMTLLM()
        
        # Test simple
        test_response = llm.generate("Test de connexion. Réponds uniquement par 'OK'.")
        logger.info(f"✅ LLM testé avec succès: {test_response.text[:50]}...")
        
        return llm
    except Exception as e:
        logger.error(f"❌ Erreur initialisation LLM: {e}")
        raise

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("🧪 Test du module LLM...")
    
    try:
        # Info provider
        info = get_provider_info()
        print(f"\n📋 Info LLM:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Test simple
        print(f"\n🚀 Test de génération...")
        llm = get_llm()
        response = llm.generate("Qu'est-ce que l'IMT Sénégal? Réponds en une phrase.")
        
        print(f"\n✅ Réponse reçue:")
        print(f"  Modèle: {response.model}")
        print(f"  Texte: {response.text}")
        if response.usage:
            print(f"  Tokens: {response.usage}")
        
        # Test LangChain
        print(f"\n🔗 Test LangChain...")
        langchain_llm = get_langchain_llm()
        result = langchain_llm.invoke("LangChain fonctionne-t-il?")
        print(f"  Résultat: {result[:100]}...")
        
        print("\n🎉 Tous les tests LLM sont passés!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        print("💡 Assurez-vous que:")
        print("  - Les clés API sont définies dans .env")
        print("  - Les dépendances sont installées")
        print("  - Le provider est correctement configuré")