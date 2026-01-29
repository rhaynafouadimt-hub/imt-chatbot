"""
Monitoring, tracing et observabilité pour le chatbot IMT.
Intégration avec Langfuse pour le suivi des coûts et performances.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from .config import config      # Acces à la configuration centrale
from .utils import generate_id, format_timestamp, format_duration
from functools import wraps

logger = logging.getLogger(__name__)

# ============================================================================
# CLASSES DE DONNÉES
# ============================================================================

class ActionType(Enum):
    """Types d'actions tracées."""
    LLM_CALL = "llm_call"
    RAG_SEARCH = "rag_search"
    MEMORY_SAVE = "memory_save"
    ACTION_EXECUTE = "action_execute"
    ERROR = "error"

@dataclass
class TraceEvent:
    """Événement de trace pour le monitoring."""
    event_id: str
    session_id: str
    event_type: ActionType
    timestamp: datetime
    duration_ms: float
    metadata: Dict[str, Any]
    input_data: Optional[Dict] = None
    output_data: Optional[Dict] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None

# ============================================================================
# MONITORING LOCAL (fallback sans Langfuse)
# ============================================================================

class LocalMonitor:
    """Monitoring local basique (fallback si Langfuse indisponible)."""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.traces: List[TraceEvent] = []
        self.start_time = datetime.now()
        logger.info(f"📊 LocalMonitor initialisé pour session: {session_id}")
    
    def start_trace(self, event_type: ActionType, metadata: Dict = None) -> str:
        """Démarre une trace et retourne un ID."""
        trace_id = f"{event_type.value}_{generate_id()}"
        
        self.traces.append(TraceEvent(
            event_id=trace_id,
            session_id=self.session_id,
            event_type=event_type,
            timestamp=datetime.now(),
            duration_ms=0.0,
            metadata=metadata or {},
            input_data=None,
            output_data=None
        ))
        
        return trace_id
    
    def end_trace(self, trace_id: str, output_data: Dict = None, 
                  error: str = None, tokens: int = None, cost: float = None,
                  duration_ms: float = None): # Recemment ajoutés pour geré la durée
        """Termine une trace avec les résultats."""
        for trace in self.traces:
            if trace.event_id == trace_id:
                if duration_ms is not None: # Utilise la duration ms si fournie
                    trace.duration_ms = duration_ms
                else:
                    # Ajout récent pour calculer la durée
                    trace.duration_ms = (datetime.now() - trace.timestamp).total_seconds() * 1000
                    
                trace.output_data = output_data
                trace.error = error
                trace.tokens_used = tokens
                trace.cost_estimate = cost
                break
    
    def log_llm_call(self, prompt: str, response: str, model: str, 
                    tokens_used: int, duration_ms: float):
        """Log un appel LLM."""
        trace_id = self.start_trace(
            ActionType.LLM_CALL,
            {"model": model, "prompt_length": len(prompt)}
        )
        
        self.end_trace(
            trace_id,
            output_data={"response": response[:200] + "..." if len(response) > 200 else response},
            tokens=tokens_used,
            cost=self._estimate_cost(model, tokens_used)
        )
        
        logger.info(f"🤖 LLM Call: {model}, {tokens_used}tokens, {duration_ms:.0f}ms")

    def log_llm_response(self, response: Any, duration_ms: float, prompt: str = ""):
        """
        Log une réponse LLM depuis un objet LLMResponse.
    
        Args:
            response: Objet LLMResponse (de llm.py)
            duration_ms: Durée en millisecondes
            prompt: Prompt original (optionnel)
        """
        try:
            # Extraire les infos selon le type de réponse
            if hasattr(response, 'text') and hasattr(response, 'model'):
                # C'est un LLMResponse de llm.py
                text = response.text
                model = response.model
                tokens = 0
            
                if hasattr(response, 'usage') and response.usage:
                    tokens = response.usage.get("total_tokens", 
                                response.usage.get("completion_tokens", 0) + 
                                response.usage.get("prompt_tokens", 0))
                elif hasattr(response, 'tokens_used'):
                    tokens = response.tokens_used
                
                self.log_llm_call(
                    prompt=prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    response=text[:200] + "..." if len(text) > 200 else text,
                    model=model,
                    tokens_used=tokens,
                    duration_ms=duration_ms
                )
            
            elif isinstance(response, str):
                # Réponse simple (texte)
                self.log_llm_call(
                    prompt=prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    response=response[:200] + "..." if len(response) > 200 else response,
                    model="unknown",
                    tokens_used=len(response.split()),
                    duration_ms=duration_ms
                )
            
        except Exception as e:
            logger.error(f"❌ Erreur logging LLMResponse: {e}")
            # Fallback basique
            self.log_llm_call(
                prompt=prompt[:100] if prompt else "",
                response=str(response)[:100],
                model="error",
                tokens_used=0,
                duration_ms=duration_ms
            )
    
    def log_rag_search(self, query: str, results_count: int, duration_ms: float):
        """Log une recherche RAG."""
        trace_id = self.start_trace(
            ActionType.RAG_SEARCH,
            {"query": query, "results_count": results_count}
        )
        
        self.end_trace(trace_id, output_data={"results": results_count})
        logger.info(f"🔍 RAG Search: '{query[:50]}...' → {results_count} résultats, {duration_ms:.0f}ms")
    
    def log_action(self, action_type: str, action_data: Dict, success: bool):
        """Log une action (email, formulaire)."""
        trace_id = self.start_trace(
            ActionType.ACTION_EXECUTE,
            {"action": action_type, "success": success}
        )
        
        self.end_trace(trace_id, output_data=action_data)
        logger.info(f"🎯 Action: {action_type}, success: {success}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict = None):
        """Log une erreur."""
        trace_id = self.start_trace(
            ActionType.ERROR,
            {"error_type": error_type, "context": context}
        )
        
        self.end_trace(trace_id, error=error_message)
        logger.error(f"❌ Error: {error_type} - {error_message}")
    
    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estime le coût d'un appel LLM."""
        cost_per_token = {
            "gemini-2.5-flash": 0.000075 / 1000,  # $0.075/1K tokens input
            "gemini-2.5-pro": 0.0035 / 1000,      # $3.50/1K tokens input
            "grok-beta": 0.0,                     # Gratuit actuellement
            "mistral": 0.0,                       # Local = gratuit
            "llama2": 0.0                         # Local = gratuit
        }
        
        return cost_per_token.get(model, 0.0001) * tokens
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la session."""
        llm_calls = [t for t in self.traces if t.event_type == ActionType.LLM_CALL]
        errors = [t for t in self.traces if t.event_type == ActionType.ERROR]
        
        total_tokens = sum(t.tokens_used or 0 for t in llm_calls)
        total_cost = sum(t.cost_estimate or 0 for t in llm_calls)
        
        return {
            "session_id": self.session_id,
            "start_time": format_timestamp(self.start_time),
            "total_traces": len(self.traces),
            "llm_calls": len(llm_calls),
            "rag_searches": len([t for t in self.traces if t.event_type == ActionType.RAG_SEARCH]),
            "actions_executed": len([t for t in self.traces if t.event_type == ActionType.ACTION_EXECUTE]),
            "errors": len(errors),
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(total_cost, 4),
            "session_duration": format_duration((datetime.now() - self.start_time).total_seconds())
        }
    
    def export_traces(self, filepath: str = "traces_export.json"):
        """Exporte toutes les traces en JSON."""
        export_data = {
            "metadata": self.get_session_stats(),
            "export_timestamp": datetime.now().isoformat(),
            "traces": [asdict(trace) for trace in self.traces]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"💾 Traces exportées: {filepath}")
        return filepath

# ============================================================================
# INTÉGRATION LANGFUSE (optionnel - pour plus tard)
# ============================================================================

class LangfuseMonitor:
    """Wrapper pour Langfuse (observabilité avancée)."""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.langfuse_available = False
        
        # Essayer d'importer Langfuse
        try:
            from langfuse import Langfuse

            # Utiliser le fichier config pour initialiser langfuse
            self.langfuse = Langfuse(
                secret_key=config.monitoring.LANGFUSE_SECRET_KEY,
                public_key=config.monitoring.LANGFUSE_PUBLIC_KEY,
                host=config.monitoring.LANGFUSE_HOST
            )

            self.langfuse_available = True
            logger.info("✅ Langfuse initialisé (host: {config.monitoring.LANGFUSE_HOST})")
        except ImportError:
            logger.warning("⚠️ Langfuse non installé, Installez-le avec pip install Langfuse")
        except Exception as e:
            logger.warning(f"⚠️ Erreur Langfuse: {e}")
    
    def trace_llm_call(self, **kwargs):
        """Trace un appel LLM avec Langfuse."""
        if not self.langfuse_available:
            return
        
        try:
            trace = self.langfuse.trace(
                name="llm_call",
                session_id=self.session_id,
                metadata=kwargs.get("metadata", {})
            )
            
            trace.generation(
                name=kwargs.get("model", "unknown"),
                input=kwargs.get("prompt", ""),
                output=kwargs.get("response", ""),
                metadata={
                    "tokens_used": kwargs.get("tokens_used", 0),
                    "duration_ms": kwargs.get("duration_ms", 0)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur Langfuse: {e}")

# ============================================================================
# FACTORY
# ============================================================================

def get_monitor(session_id: str = "default", use_langfuse: bool = False):
    """
    Factory pour obtenir un moniteur.
    
    Args:
        session_id: ID de la session
        use_langfuse: Utiliser Langfuse si disponible
    
    Returns:
        Object de monitoring
    """
    if use_langfuse is None:
        use_langfuse = config.monitoring.USE_LANGFUSE

    if use_langfuse:
        try:
            monitor = LangfuseMonitor(session_id)
            if monitor.langfuse_available:
                return monitor
        except Exception as e:
            logger.warning(f"⚠️ langfuse non disponible, fallback local:{e}")
    
    return LocalMonitor(session_id)

# ============================================================================
# DÉCORATEURS POUR FACILITÉ
# ============================================================================

def trace_operation(operation_type: ActionType):
    """Décorateur pour tracer automatiquement une fonction."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'monitor'):
                return func(self, *args, **kwargs)
            
            start_time = time.time()
            trace_id = self.monitor.start_trace(
                operation_type,
                {"function": func.__name__, "args_count": len(args)}
            )
            
            try:
                result = func(self, *args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                self.monitor.end_trace(
                    trace_id,
                    output_data={"success": True, "result_type": type(result).__name__},
                    duration_ms=duration_ms
                )
                
                return result
                
            except Exception as e:
                self.monitor.end_trace(
                    trace_id,
                    error=str(e),
                    duration_ms=(time.time() - start_time) * 1000
                )
                raise
        
        return wrapper
    return decorator

def monitor_llm_call(func):
    """
    Décorateur spécifique pour les appels LLM.
    À utiliser dans llm.py sur les méthodes generate().
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Vérifier si un monitor est disponible
        monitor = None
        if hasattr(self, 'monitor'):
            monitor = self.monitor
        elif 'monitor' in kwargs:
            monitor = kwargs['monitor']
        
        start_time = time.time()
        
        # Exécuter la fonction
        result = func(self, *args, **kwargs)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Logger si monitor disponible
        if monitor and hasattr(monitor, 'log_llm_response'):
            # Extraire le prompt (premier argument ou kwargs)
            prompt = ""
            if args and isinstance(args[0], str):
                prompt = args[0]
            elif 'prompt' in kwargs:
                prompt = kwargs['prompt']
            
            monitor.log_llm_response(
                response=result,
                duration_ms=duration_ms,
                prompt=prompt
            )
        
        return result
    
    return wrapper

# ============================================================================
# INTÉGRATION CHAINLIT (pour l'interface)
# ============================================================================

def get_chainlit_monitor():
    """
    Crée un moniteur configuré pour Chainlit.
    Utilise l'ID de session de Chainlit si disponible.
    """
    try:
        import chainlit as cl
        session_id = cl.user_session.get("id", "chainlit_session")
    except:
        session_id = "web_session"
    
    return get_monitor(session_id)

def log_to_chainlit(message: str, level: str = "info"):
    """
    Log un message à la fois dans Chainlit et dans le système.
    Utile pour l'interface utilisateur.
    """
    logger.log(getattr(logging, level.upper()), message)
    
    try:
        import chainlit as cl
        cl.Message(
            content=f"[{level.upper()}] {message}",
            author="System"
        ).send()
    except:
        pass  # Chainlit non disponible
# Test
if __name__ == "__main__":
    print("📊 Test du monitoring...")
    
    monitor = LocalMonitor("test_session")
    
    # Simuler des traces
    monitor.log_llm_call(
        prompt="Bonjour",
        response="Bonjour, comment puis-je vous aider ?",
        model="gemini-2.5-flash",
        tokens_used=150,
        duration_ms=1200
    )
    
    monitor.log_rag_search(
        query="frais de scolarité",
        results_count=3,
        duration_ms=450
    )
    
    monitor.log_error(
        error_type="API Error",
        error_message="Connection timeout",
        context={"endpoint": "https://api.imt.sn"}
    )
    
    # Afficher les stats
    stats = monitor.get_session_stats()
    print(f"\n📈 Statistiques:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Test monitoring terminé")