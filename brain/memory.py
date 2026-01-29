import redis
from typing import Optional, List, Dict, Any
from datetime import datetime  # ← IMPORT AJOUTÉ
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
import json
import os
import warnings

class MemoryManager:
    def __init__(self, session_id: str = "default", use_redis: bool = True, 
                 redis_url: str = "redis://localhost:6379/0"):
        """
        Gestionnaire de mémoire pour le chatbot IMT.
        
        Args:
            session_id: Identifiant unique de la session utilisateur
            use_redis: Utiliser Redis si True, sinon mémoire locale
            redis_url: URL de connexion Redis
        """
        self.session_id = session_id
        self.use_redis = use_redis
        self.redis_url = redis_url
        self.memory = self._initialize_memory()
    
    def _initialize_memory(self) -> ConversationBufferMemory:
        """Initialise la mémoire Redis ou locale"""
        if self.use_redis:
            try:
                # Test connexion Redis
                redis_client = redis.Redis.from_url(
                    self.redis_url,
                    socket_connect_timeout=2,
                    socket_keepalive=True,
                    retry_on_timeout=True
                )
                redis_client.ping()
                
                # Configuration Redis pour LangChain
                # Note: LangChain stocke avec le préfixe "message_store:"
                chat_history = RedisChatMessageHistory(
                    session_id=self.session_id,
                    url=self.redis_url,
                    key_prefix="imt_chatbot:"  # ← PRÉFIXE PERSONNALISÉ
                )
                
                # Mémoire de conversation
                conversation_memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    chat_memory=chat_history,
                    return_messages=True,
                    input_key="input",
                    output_key="output",
                    human_prefix="Utilisateur",
                    ai_prefix="Assistant IMT"
                )
                
                print(f"✅ Mémoire Redis initialisée (session: {self.session_id})")
                return conversation_memory
                
            except (redis.ConnectionError, redis.TimeoutError, redis.AuthenticationError) as e:
                print(f"⚠️ Redis non disponible: {e}, utilisation mémoire locale")
                self.use_redis = False
                warnings.warn(f"Redis connection failed: {e}")
        
        # Fallback: mémoire locale
        print(f"📝 Utilisation mémoire locale (session: {self.session_id})")
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output",
            human_prefix="Utilisateur",
            ai_prefix="Assistant IMT"
        )
    
    def save_conversation(self, user_input: str, ai_response: str) -> None:
        """Sauvegarde un échange dans la mémoire"""
        try:
            self.memory.save_context(
                {"input": user_input},
                {"output": ai_response}
            )
        except Exception as e:
            print(f"❌ Erreur sauvegarde conversation: {e}")
            # Recréer la mémoire en cas d'erreur
            self.memory = self._initialize_memory()
            # Réessayer
            self.memory.save_context(
                {"input": user_input},
                {"output": ai_response}
            )
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Récupère l'historique des conversations"""
        try:
            messages = self.memory.chat_memory.messages
            
            if not messages:
                return []
            
            if limit and limit > 0:
                # Prendre les derniers échanges complets
                start_idx = max(0, len(messages) - (limit * 2))
                messages = messages[start_idx:]
            
            history = []
            # Parcourir par paires (user, assistant)
            for i in range(0, len(messages) - 1, 2):
                if i + 1 < len(messages):
                    user_msg = messages[i]
                    ai_msg = messages[i + 1]
                    
                    # Vérifier que c'est bien une paire user/assistant
                    if hasattr(user_msg, 'type') and hasattr(ai_msg, 'type'):
                        history.append({
                            "user": user_msg.content,
                            "assistant": ai_msg.content,
                            "timestamp": datetime.now().isoformat()
                        })
            
            return history
            
        except Exception as e:
            print(f"❌ Erreur récupération historique: {e}")
            return []
    
    def get_context_for_prompt(self, last_n: int = 3) -> str:
        """Formate l'historique pour inclusion dans un prompt"""
        history = self.get_conversation_history(limit=last_n)
        
        if not history:
            return "Aucun historique de conversation."
        
        context_parts = ["Historique récent de la conversation:"]
        for idx, exchange in enumerate(history, 1):
            context_parts.append(f"\nÉchange {idx}:")
            context_parts.append(f"👤 Utilisateur: {exchange['user']}")
            context_parts.append(f"🤖 Assistant IMT: {exchange['assistant']}")
        
        return "\n".join(context_parts)
    
    def clear_memory(self) -> bool:
        """Efface la mémoire de la session"""
        try:
            if self.use_redis:
                redis_client = redis.Redis.from_url(self.redis_url)
                
                # Méthode 1: Via RedisChatMessageHistory
                chat_history = RedisChatMessageHistory(
                    session_id=self.session_id,
                    url=self.redis_url,
                    key_prefix="imt_chatbot:"
                )
                chat_history.clear()
                
                # Méthode 2: Nettoyage manuel des clés
                pattern = f"imt_chatbot:*:{self.session_id}"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            
            # Effacer la mémoire locale
            self.memory.clear()
            
            print(f"🗑️ Mémoire effacée pour la session: {self.session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur effacement mémoire: {e}")
            return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """Retourne des informations sur la session"""
        history = self.get_conversation_history()
        
        info = {
            "session_id": self.session_id,
            "memory_backend": "redis" if self.use_redis else "local",
            "conversation_count": len(history),
            "total_messages": len(self.memory.chat_memory.messages) if hasattr(self.memory.chat_memory, 'messages') else 0,
            "created_at": datetime.now().isoformat(),
            "redis_available": self.use_redis
        }
        
        if history:
            info["last_interaction"] = {
                "user": history[-1]["user"][:100] + "..." if len(history[-1]["user"]) > 100 else history[-1]["user"],
                "assistant": history[-1]["assistant"][:100] + "..." if len(history[-1]["assistant"]) > 100 else history[-1]["assistant"],
                "timestamp": history[-1].get("timestamp", "N/A")
            }
        
        return info
    
    def export_memory(self, filepath: Optional[str] = None) -> str:
        """Exporte la mémoire dans un fichier JSON"""
        if filepath is None:
            os.makedirs("exports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"exports/memory_{self.session_id}_{timestamp}.json"
        
        history = self.get_conversation_history()
        session_info = self.get_session_info()
        
        data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "project": "IMT Chatbot Assistant",
                "version": "1.0"
            },
            "session_info": session_info,
            "conversations": history
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Mémoire exportée vers: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Erreur export mémoire: {e}")
            return ""
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur la mémoire"""
        messages = self.memory.chat_memory.messages if hasattr(self.memory.chat_memory, 'messages') else []
        
        total_chars = sum(len(msg.content) for msg in messages if hasattr(msg, 'content'))
        total_words = sum(len(msg.content.split()) for msg in messages if hasattr(msg, 'content'))
        
        return {
            "total_messages": len(messages),
            "total_conversations": len(messages) // 2,
            "total_characters": total_chars,
            "total_words": total_words,
            "avg_words_per_message": total_words / len(messages) if messages else 0
        }

# Cache des gestionnaires de mémoire par session
_memory_managers: Dict[str, MemoryManager] = {}

def get_memory_manager(session_id: str = "default", **kwargs) -> MemoryManager:
    """
    Factory pour obtenir un gestionnaire de mémoire.
    Utilise un cache par session_id.
    
    Args:
        session_id: ID de la session
        **kwargs: Arguments passés à MemoryManager
    
    Returns:
        MemoryManager: Gestionnaire de mémoire
    """
    if session_id not in _memory_managers:
        _memory_managers[session_id] = MemoryManager(session_id=session_id, **kwargs)
    
    return _memory_managers[session_id]

def clear_all_memory() -> Dict[str, bool]:
    """
    Efface toutes les mémoires de toutes les sessions.
    Utilisé pour le nettoyage ou les tests.
    
    Returns:
        Dict: Résultats par session
    """
    results = {}
    for session_id, manager in _memory_managers.items():
        results[session_id] = manager.clear_memory()
    
    _memory_managers.clear()
    return results

# Test rapide
if __name__ == "__main__":
    print("🧠 Test du MemoryManager...")
    
    # Test avec mémoire locale
    mm = MemoryManager(session_id="test_session", use_redis=False)
    
    # Sauvegarde test
    mm.save_conversation("Bonjour", "Bonjour ! Comment puis-je vous aider ?")
    mm.save_conversation("Qu'est-ce que l'IMT ?", "L'IMT est un institut...")
    
    # Vérification
    history = mm.get_conversation_history()
    print(f"📝 Historique: {len(history)} échanges")
    
    info = mm.get_session_info()
    print(f"📊 Info session: {info}")
    
    # Export test
    export_path = mm.export_memory()
    if export_path:
        print(f"✅ Export réussi: {export_path}")
    
    print("✅ Tests mémoire terminés")