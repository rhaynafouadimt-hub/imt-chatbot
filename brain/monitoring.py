"""
Monitoring, tracing et observabilité pour le chatbot IMT.
Intégration avec Langfuse 3.13.0 + OpenTelemetry pour le suivi des coûts et performances.
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
                  duration_ms: float = None):
        """Termine une trace avec les résultats."""
        for trace in self.traces:
            if trace.event_id == trace_id:
                if duration_ms is not None:
                    trace.duration_ms = duration_ms
                else:
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
        """
        try:
            if hasattr(response, 'text') and hasattr(response, 'model'):
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
                self.log_llm_call(
                    prompt=prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    response=response[:200] + "..." if len(response) > 200 else response,
                    model="unknown",
                    tokens_used=len(response.split()),
                    duration_ms=duration_ms
                )
            
        except Exception as e:
            logger.error(f"❌ Erreur logging LLMResponse: {e}")
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
            "gemini-2.5-flash": 0.000075 / 1000,
            "gemini-2.5-pro": 0.0035 / 1000,
            "grok-beta": 0.0,
            "mistral": 0.0,
            "llama2": 0.0
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
# INTÉGRATION LANGFUSE 3.13.0 + OPENTELEMETRY
# ============================================================================

class LangfuseMonitor:
    """Wrapper pour Langfuse 3.13.0 avec OpenTelemetry."""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.langfuse_available = False
        self.langfuse = None
        self.tracer = None  # OpenTelemetry Tracer
    
        logger.debug(f"🔧 Initialisation LangfuseMonitor pour session: {session_id}")
    
        # Vérifier que Langfuse est activé dans la config
        if not config.monitoring.USE_LANGFUSE:
            logger.warning("⚠️ Langfuse désactivé dans la configuration (USE_LANGFUSE=False)")
            return
    
        # Vérifier les clés
        if not config.monitoring.LANGFUSE_SECRET_KEY:
            logger.warning("⚠️ LANGFUSE_SECRET_KEY manquante")
            return
    
        if not config.monitoring.LANGFUSE_PUBLIC_KEY:
            logger.warning("⚠️ LANGFUSE_PUBLIC_KEY manquante")
            return
    
        logger.debug(f"🔧 Clés Langfuse présentes")
    
        # Essayer d'importer et d'initialiser
        try:
            from langfuse import Langfuse
            from opentelemetry import trace
            from opentelemetry.trace import StatusCode
        
            logger.info(f"🔧 Initialisation Langfuse 3.13.0 avec host: {config.monitoring.LANGFUSE_HOST}")
        
            self.langfuse = Langfuse(
                secret_key=config.monitoring.LANGFUSE_SECRET_KEY,
                public_key=config.monitoring.LANGFUSE_PUBLIC_KEY,
                host=config.monitoring.LANGFUSE_HOST
            )
        
            # Initialiser OpenTelemetry Tracer
            self.tracer = trace.get_tracer("imt_chatbot")
        
            self.langfuse_available = True
            logger.info(f"✅ Langfuse 3.13.0 + OpenTelemetry initialisés")
            logger.info(f"✅ Tracer OpenTelemetry: {self.tracer}")
        
        except ImportError as e:
            logger.error(f"❌ ImportError Langfuse/OpenTelemetry: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation Langfuse: {e}")
    
    def _create_span(self, span_name: str, attributes: Dict[str, Any], events: List[Dict] = None):
        """Créer un span OpenTelemetry avec les attributs donnés."""
        if not self.langfuse_available or not self.tracer:
            return None
        
        try:
            from opentelemetry.trace import StatusCode
            
            with self.tracer.start_as_current_span(span_name) as span:
                # Ajouter les attributs de base
                base_attrs = {
                    "langfuse.session.id": self.session_id,
                    "langfuse.project": "imt_chatbot",
                    "project.name": "IMT Chatbot",
                    "project.module": "brain",
                    "environment": "development"
                }
                
                # Fusionner avec les attributs spécifiques
                all_attrs = {**base_attrs, **attributes}
                span.set_attributes(all_attrs)
                
                # Ajouter les événements
                if events:
                    for event in events:
                        span.add_event(event["name"], event.get("attributes", {}))
                
                # Marquer comme réussi
                span.set_status(StatusCode.OK)
                
                # Créer un ID de trace Langfuse
                if hasattr(self.langfuse, 'create_trace_id'):
                    trace_id = self.langfuse.create_trace_id()
                    span.set_attribute("langfuse.trace.id", trace_id)
                    return trace_id
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur création span OpenTelemetry: {e}")
            return None
    
    def log_llm_response(self, response: Any, duration_ms: float, prompt: str = ""):
        """
        Log une réponse LLM vers Langfuse via OpenTelemetry.
        """
        if not self.langfuse_available or not self.tracer:
            logger.warning(f"⚠️ Langfuse/OpenTelemetry non disponible pour logging")
            return
    
        try:
            # Extraction des infos
            if hasattr(response, 'text') and hasattr(response, 'model'):
                text = response.text
                model = response.model
                tokens = 0
            
                if hasattr(response, 'usage') and response.usage:
                    tokens = response.usage.get("total_tokens", 
                        response.usage.get("completion_tokens", 0) + 
                        response.usage.get("prompt_tokens", 0))
                elif hasattr(response, 'tokens_used'):
                    tokens = response.tokens_used
            elif isinstance(response, str):
                text = response
                model = "unknown"
                tokens = len(text.split())
            else:
                text = str(response)
                model = "unknown"
                tokens = 0

            logger.info(f"📤 Envoi trace LLM OpenTelemetry: model={model}, duration={duration_ms}ms")
        
            # Créer le span avec tous les attributs
            attributes = {
                "llm.model": model,
                "llm.provider": "gemini",
                "llm.duration_ms": float(duration_ms),
                "llm.tokens_used": tokens,
                "llm.prompt_length": len(prompt) if prompt else 0,
                "llm.response_length": len(text) if text else 0,
            }
            
            events = [
                {
                    "name": "llm.generation.start",
                    "attributes": {"timestamp": time.time()}
                }
            ]
            
            if prompt:
                events.append({
                    "name": "llm.prompt",
                    "attributes": {
                        "content": prompt[:300] + ("..." if len(prompt) > 300 else ""),
                        "full_length": len(prompt)
                    }
                })
            
            if text:
                events.append({
                    "name": "llm.response",
                    "attributes": {
                        "content": text[:500] + ("..." if len(text) > 500 else ""),
                        "full_length": len(text)
                    }
                })
            
            events.append({
                "name": "llm.generation.end",
                "attributes": {
                    "timestamp": time.time(),
                    "duration_ms": duration_ms,
                    "success": True
                }
            })
            
            trace_id = self._create_span(
                span_name="imt_chatbot_llm_call",
                attributes=attributes,
                events=events
            )
            
            if trace_id:
                logger.info(f"✅ Trace LLM OpenTelemetry envoyée: {model}, trace_id={trace_id[:12]}...")
            
            # Flush les données
            self._flush_langfuse()
    
        except Exception as e:
            logger.error(f"❌ Erreur OpenTelemetry log_llm_response: {e}", exc_info=True)
    
    def log_rag_search(self, query: str, results_count: int, duration_ms: float):
        """
        Log une recherche RAG vers Langfuse via OpenTelemetry.
        """
        if not self.langfuse_available or not self.tracer:
            return
    
        try:
            logger.info(f"🔍 Envoi trace RAG OpenTelemetry: '{query[:30]}...'")
        
            attributes = {
                "rag.query": query[:100],
                "rag.results_count": results_count,
                "rag.duration_ms": float(duration_ms),
                "component": "rag"
            }
            
            events = [
                {
                    "name": "rag.search",
                    "attributes": {
                        "query": query[:200],
                        "results_count": results_count
                    }
                }
            ]
            
            trace_id = self._create_span(
                span_name="imt_chatbot_rag_search",
                attributes=attributes,
                events=events
            )
            
            if trace_id:
                logger.info(f"✅ Trace RAG OpenTelemetry envoyée, trace_id={trace_id[:12]}...")
            
            self._flush_langfuse()
        
        except Exception as e:
            logger.error(f"❌ Erreur RAG logging: {e}")
    
    def log_action(self, action_type: str, action_data: Dict, success: bool):
        """
        Log une action vers Langfuse via OpenTelemetry.
        """
        if not self.langfuse_available or not self.tracer:
            return
    
        try:
            logger.info(f"🎯 Envoi trace action OpenTelemetry: {action_type}")
        
            attributes = {
                "action.type": action_type,
                "action.success": success,
                "component": "action"
            }
            
            events = [
                {
                    "name": "action.execute",
                    "attributes": {
                        "type": action_type,
                        "success": success,
                        "data": str(action_data)[:200]  # Limité
                    }
                }
            ]
            
            trace_id = self._create_span(
                span_name="imt_chatbot_action",
                attributes=attributes,
                events=events
            )
            
            if trace_id:
                logger.info(f"✅ Trace action OpenTelemetry envoyée, trace_id={trace_id[:12]}...")
            
            self._flush_langfuse()
        
        except Exception as e:
            logger.error(f"❌ Erreur action logging: {e}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict = None):
        """
        Log une erreur vers Langfuse via OpenTelemetry.
        """
        if not self.langfuse_available or not self.tracer:
            return
    
        try:
            from opentelemetry.trace import StatusCode
            
            logger.error(f"❌ Envoi trace erreur OpenTelemetry: {error_type}")
        
            with self.tracer.start_as_current_span("imt_chatbot_error") as span:
                # Attributs de base
                span.set_attributes({
                    "langfuse.session.id": self.session_id,
                    "langfuse.project": "imt_chatbot",
                    "error.type": error_type,
                    "error.message": error_message[:500],
                    "component": "error",
                    "project.name": "IMT Chatbot",
                    "environment": "development"
                })
                
                # Ajouter le contexte si disponible
                if context:
                    span.add_event("error.context", {
                        "data": str(context)[:200]
                    })
                
                # Marquer comme erreur
                span.set_status(StatusCode.ERROR, error_message)
                
                # ID de trace
                if hasattr(self.langfuse, 'create_trace_id'):
                    trace_id = self.langfuse.create_trace_id()
                    span.set_attribute("langfuse.trace.id", trace_id)
            
            logger.info(f"✅ Trace erreur OpenTelemetry envoyée")
            
            self._flush_langfuse()
        
        except Exception as e:
            logger.error(f"❌ Erreur error logging: {e}")
    
    def _flush_langfuse(self):
        """Forcer l'envoi des données à Langfuse."""
        try:
            if hasattr(self.langfuse, 'flush'):
                self.langfuse.flush()
                logger.debug("🔄 Données flushées vers Langfuse")
        except Exception as e:
            logger.debug(f"ℹ️ Flush non disponible: {e}")
    
    # Méthodes de compatibilité pour le décorateur @trace_operation
    def start_trace(self, event_type: ActionType, metadata: Dict = None):
        """
        Démarre une trace (pour compatibilité avec le décorateur).
        Retourne un ID de trace temporaire.
        """
        trace_id = f"otel_{event_type.value}_{int(time.time() * 1000)}"
        logger.debug(f"📝 Début trace OpenTelemetry: {trace_id}")
        return trace_id
    
    def end_trace(self, trace_id: str, output_data: Dict = None, 
                  error: str = None, tokens: int = None, cost: float = None,
                  duration_ms: float = None):
        """
        Termine une trace (méthode factice pour compatibilité).
        Les vraies traces sont envoyées directement via les méthodes spécifiques.
        """
        logger.debug(f"📝 Fin trace OpenTelemetry: {trace_id}")

# ============================================================================
# FACTORY
# ============================================================================

def get_monitor(session_id: str = "default", use_langfuse: bool = None):
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
    
    logger.info(f"🔧 Demande moniteur: session={session_id}, langfuse={use_langfuse}")
    
    if use_langfuse:
        try:
            monitor = LangfuseMonitor(session_id)
            if monitor.langfuse_available:
                logger.info("✅ LangfuseMonitor sélectionné")
                return monitor
            else:
                logger.warning("⚠️ LangfuseMonitor non disponible, fallback local")
        except Exception as e:
            logger.error(f"❌ Erreur création LangfuseMonitor: {e}")
    
    # Fallback local
    logger.info("📊 LocalMonitor sélectionné (fallback)")
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

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("🧪 TEST LANGFUSE 3.13.0 + OPENTELEMETRY")
    print("=" * 50)
    
    # Test 1: LocalMonitor (fallback)
    print("\n1. Test LocalMonitor (fallback):")
    local_monitor = LocalMonitor("test_local")
    local_monitor.log_llm_call(
        prompt="Test local",
        response="Réponse locale",
        model="local-model",
        tokens_used=100,
        duration_ms=500
    )
    
    # Test 2: LangfuseMonitor
    print("\n2. Test LangfuseMonitor:")
    langfuse_monitor = LangfuseMonitor("test_langfuse")
    print(f"   Langfuse disponible: {langfuse_monitor.langfuse_available}")
    print(f"   Tracer disponible: {langfuse_monitor.tracer is not None}")
    
    if langfuse_monitor.langfuse_available:
        # Simuler une réponse LLM
        class MockResponse:
            text = "Ceci est un test OpenTelemetry avec Langfuse 3.13.0"
            model = "gemini-2.5-flash-test"
            usage = {"prompt_tokens": 20, "completion_tokens": 30}
        
        print("   📤 Envoi d'une trace OpenTelemetry...")
        langfuse_monitor.log_llm_response(
            response=MockResponse(),
            duration_ms=750,
            prompt="Test de l'API OpenTelemetry avec Langfuse"
        )
        print("   ✅ Trace envoyée (vérifie sur https://cloud.langfuse.com)")
        
        # Tester RAG
        print("\n   🔍 Test trace RAG...")
        langfuse_monitor.log_rag_search(
            query="frais de scolarité IMT",
            results_count=3,
            duration_ms=450
        )
    else:
        print("   ❌ Langfuse/OpenTelemetry non disponible")
    
    # Test 3: Via factory
    print("\n3. Test via get_monitor():")
    factory_monitor = get_monitor("test_factory", use_langfuse=True)
    print(f"   Type: {type(factory_monitor).__name__}")
    print(f"   Langfuse disponible: {getattr(factory_monitor, 'langfuse_available', False)}")
    
    print("\n✅ Tests monitoring terminés")