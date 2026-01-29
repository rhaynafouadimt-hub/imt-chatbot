"""
Interface RAG simplifiée pour l'orchestrateur.
Ce module fait l'interface avec le système RASG qui sera implémenté par un autre membre.
"""

from typing import List, Dict, Optional, Any
import requests
import json
from datetime import datetime
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ============================================================================
# INTERFACE ABSTRAITE
# ============================================================================

class IRAGSystem(ABC):
    """Interface abstraite pour le système RAG."""
    
    @abstractmethod
    def search(self, query: str, k: int = 4) -> List[Dict]:
        """Recherche des informations pertinentes."""
        pass
    
    @abstractmethod
    def get_context_for_question(self, question: str) -> str:
        """Récupère le contexte formaté pour une question."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système RAG."""
        pass

# ============================================================================
# IMPLÉMENTATION MOCK (pour le développement)
# ============================================================================

class MockRAGSystem(IRAGSystem):
    """
    Mock du système RAG pour le développement.
    À remplacer par l'implémentation réelle de votre collègue.
    """
    
    def __init__(self):
        self.mock_data = self._load_mock_data()
        logger.info("✅ Mock RAG system initialisé (pour développement)")
    
    def _load_mock_data(self) -> List[Dict]:
        """Charge des données mock pour l'IMT."""
        return [
            {
                "id": 1,
                "title": "Formations à l'IMT",
                "content": "L'IMT propose des formations en Licence et Master dans les domaines du Management, de l'Informatique et des Technologies. Les programmes sont conçus pour répondre aux besoins du marché.",
                "category": "formations",
                "source": "https://www.imt.sn/formations",
                "relevance": 0.95
            },
            {
                "id": 2,
                "title": "Frais de scolarité",
                "content": "Les frais de scolarité varient selon les formations. Pour une licence: 500.000 FCFA par an. Pour un master: 750.000 FCFA par an. Des bourses sont disponibles pour les meilleurs étudiants.",
                "category": "frais",
                "source": "https://www.imt.sn/frais",
                "relevance": 0.92
            },
            {
                "id": 3,
                "title": "Admission et inscriptions",
                "content": "Les admissions se font sur étude de dossier. Les dossiers doivent être déposés entre janvier et mars pour la rentrée de septembre. Prérequis: Baccalauréat pour la licence, Licence pour le master.",
                "category": "admission",
                "source": "https://www.imt.sn/admission",
                "relevance": 0.88
            },
            {
                "id": 4,
                "title": "Campus et localisation",
                "content": "L'IMT est situé à Dakar, Sacré-Cœur. Le campus dispose de salles de classe modernes, d'une bibliothèque, de laboratoires informatiques et d'espaces de détente pour les étudiants.",
                "category": "campus",
                "source": "https://www.imt.sn/campus",
                "relevance": 0.85
            },
            {
                "id": 5,
                "title": "Contact et informations",
                "content": "Email: contact@imt.sn | Téléphone: +221 33 123 45 67 | Adresse: Rue de l'Université, Dakar. Horaires d'ouverture: Lundi-Vendredi, 8h-18h.",
                "category": "contact",
                "source": "https://www.imt.sn/contact",
                "relevance": 0.82
            }
        ]
    
    def search(self, query: str, k: int = 4) -> List[Dict]:
        """Recherche mock basée sur des mots-clés simples."""
        query_lower = query.lower()
        results = []
        
        # Filtrage simple par mots-clés
        for doc in self.mock_data:
            score = self._calculate_similarity(query_lower, doc)
            if score > 0.3:  # Seuil minimal
                results.append({
                    "content": doc["content"],
                    "score": score,
                    "metadata": {
                        "source": doc["source"],
                        "title": doc["title"],
                        "category": doc["category"],
                        "doc_id": doc["id"]
                    },
                    "preview": doc["content"][:150] + "..."
                })
        
        # Trier par score et limiter
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    
    def _calculate_similarity(self, query: str, doc: Dict) -> float:
        """Calcule une similarité simple basée sur les mots-clés."""
        keywords = {
            "formation": ["formation", "programme", "cours", "étude", "licence", "master"],
            "frais": ["frais", "coût", "tarif", "prix", "scolarité", "bourse"],
            "admission": ["admission", "inscription", "dossier", "concours", "sélection"],
            "contact": ["contact", "email", "téléphone", "adresse", "localisation"],
            "campus": ["campus", "localisation", "adresse", "bâtiment", "salle"]
        }
        
        # Vérifier la catégorie du document
        doc_category = doc.get("category", "")
        
        # Vérifier si des mots-clés de la catégorie sont dans la requête
        if doc_category in keywords:
            category_keywords = keywords[doc_category]
            for keyword in category_keywords:
                if keyword in query:
                    return doc.get("relevance", 0.8)
        
        # Similarité basée sur le contenu (simple)
        content = doc.get("content", "").lower()
        query_words = set(query.split())
        content_words = set(content.split())
        
        common_words = query_words.intersection(content_words)
        if query_words:
            return len(common_words) / len(query_words) * 0.5
        return 0.0
    
    def get_context_for_question(self, question: str, max_results: int = 3) -> str:
        """Retourne le contexte formaté pour une question."""
        results = self.search(question, k=max_results)
        
        if not results:
            return "Aucune information spécifique trouvée dans la base de connaissances de l'IMT."
        
        # Formater le contexte
        context_parts = ["📚 Informations pertinentes de l'IMT:"]
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            context_parts.append(
                f"\n{i}. [{metadata.get('category', 'INFO').upper()}] {metadata.get('title', 'Sans titre')}"
            )
            context_parts.append(f"   📄 {result['content'][:300]}...")
        
        context_parts.append(f"\n📊 {len(results)} informations pertinentes trouvées.")
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du mock."""
        return {
            "status": "mock_mode",
            "total_documents": len(self.mock_data),
            "last_updated": datetime.now().isoformat(),
            "note": "Ceci est un mock. À remplacer par l'implémentation RAG réelle."
        }

# ============================================================================
# CLIENT API (pour l'intégration avec le RAG de votre collègue)
# ============================================================================

class RAGAPIClient(IRAGSystem):
    """
    Client pour le système RAG exposé via API.
    Votre collègue exposera son RAG via une API REST.
    """
    
    def __init__(self, api_url: str = "http://localhost:8000/api/rag"):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.timeout = 10
        logger.info(f"✅ RAG API Client initialisé: {api_url}")
    
    def search(self, query: str, k: int = 4) -> List[Dict]:
        """Appelle l'API de recherche du système RAG."""
        try:
            payload = {
                "query": query,
                "k": k,
                "filters": {}  # Peut être étendu avec des filtres
            }
            
            response = self.session.post(
                f"{self.api_url}/search",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("results", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur API RAG: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur traitement réponse RAG: {e}")
            return []
    
    def get_context_for_question(self, question: str) -> str:
        """Récupère le contexte formaté via API."""
        try:
            payload = {"question": question}
            
            response = self.session.post(
                f"{self.api_url}/context",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("context", "Contexte non disponible.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur API contexte: {e}")
            return f"Erreur de connexion au système RAG: {str(e)}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du système RAG via API."""
        try:
            response = self.session.get(f"{self.api_url}/stats")
            response.raise_for_status()
            return response.json()
        except:
            return {"status": "api_unavailable", "error": "Impossible de contacter le serveur RAG"}

# ============================================================================
# FACTORY PRINCIPALE
# ============================================================================

class RAGSystemFactory:
    """
    Factory pour créer l'instance RAG appropriée.
    Basculera entre Mock, API, ou autre implémentation.
    """
    
    @staticmethod
    def create(rag_mode: str = "mock", **kwargs) -> IRAGSystem:
        """
        Crée une instance du système RAG.
        
        Args:
            rag_mode: "mock", "api", ou "direct"
            **kwargs: Arguments spécifiques au mode
        
        Returns:
            IRAGSystem: Instance du système RAG
        """
        if rag_mode == "api":
            api_url = kwargs.get("api_url", "http://localhost:8000/api/rag")
            return RAGAPIClient(api_url=api_url)
        
        elif rag_mode == "direct":
            # Ici, vous pourriez importer l'implémentation directe de votre collègue
            # from team_member.rag import RealRAGSystem
            # return RealRAGSystem(**kwargs)
            logger.warning("Mode 'direct' non implémenté. Utilisation du mock.")
            return MockRAGSystem()
        
        else:  # mock par défaut
            logger.info("Utilisation du mode MOCK pour le RAG (développement)")
            return MockRAGSystem()

# ============================================================================
# CLASSE PRINCIPALE D'ORCHESTRATION
# ============================================================================

class RAGOrchestrator:
    """
    Orchestrateur pour le système RAG.
    Gère l'interaction avec le RAG et formatage pour le LLM.
    """
    
    def __init__(self, rag_mode: str = "mock", **kwargs):
        """
        Initialise l'orchestrateur RAG.
        
        Args:
            rag_mode: Mode de fonctionnement ("mock", "api", "direct")
            **kwargs: Arguments pour la factory
        """
        self.rag_mode = rag_mode
        self.rag_system = RAGSystemFactory.create(rag_mode, **kwargs)
        
        # Configuration
        self.default_k = 4  # Nombre par défaut de résultats
        self.context_max_length = 2000  # Caractères max pour le contexte
        
        logger.info(f"✅ RAGOrchestrator initialisé en mode: {rag_mode}")
    
    def answer_with_context(self, question: str) -> Dict[str, Any]:
        """
        Répond à une question avec contexte RAG.
        
        Args:
            question: Question de l'utilisateur
            
        Returns:
            Dict: Réponse complète avec contexte et métadonnées
        """
        logger.info(f"🔍 Traitement question RAG: '{question}'")
        
        # 1. Rechercher des informations pertinentes
        search_results = self.rag_system.search(question, k=self.default_k)
        
        # 2. Formater le contexte
        if search_results:
            context = self._format_context(search_results)
            confidence = self._calculate_confidence(search_results)
        else:
            context = "Aucune information spécifique trouvée sur le site de l'IMT."
            confidence = 0.0
        
        # 3. Préparer la réponse
        response = {
            "question": question,
            "context": context,
            "has_context": len(search_results) > 0,
            "results_count": len(search_results),
            "confidence": confidence,
            "rag_mode": self.rag_mode,
            "timestamp": datetime.now().isoformat(),
            "suggested_prompt": self._create_prompt_suggestion(question, context)
        }
        
        # 4. Ajouter les résultats bruts si demandé
        if logger.level == logging.DEBUG:
            response["raw_results"] = search_results
        
        return response
    
    def _format_context(self, results: List[Dict]) -> str:
        """Formate les résultats de recherche en contexte lisible."""
        context_parts = ["📚 Informations de l'IMT (source: site web):"]
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            score = result.get("score", 0)
            
            # Formater une entrée
            entry = [
                f"\n{i}. [{metadata.get('category', 'INFO').upper()}] {metadata.get('title', 'Sans titre')}",
                f"   Confiance: {score:.1%}",
                f"   Source: {metadata.get('source', 'N/A')}",
                f"   📄 {result.get('content', '')[:400]}..."
            ]
            
            context_parts.extend(entry)
        
        context_parts.append(f"\n📊 {len(results)} informations pertinentes extraites.")
        
        return "\n".join(context_parts)
    
    def _calculate_confidence(self, results: List[Dict]) -> float:
        """Calcule un score de confiance basé sur les résultats."""
        if not results:
            return 0.0
        
        # Moyenne des scores, pondérée par le nombre de résultats
        scores = [r.get("score", 0) for r in results]
        avg_score = sum(scores) / len(scores)
        
        # Ajuster par le nombre de résultats (plus de résultats = plus de confiance)
        count_factor = min(len(results) / 3, 1.0)  # Max 1.0 pour 3+ résultats
        
        return min(avg_score * count_factor, 1.0)
    
    def _create_prompt_suggestion(self, question: str, context: str) -> str:
        """Crée une suggestion de prompt pour le LLM."""
        return f"""Question de l'utilisateur: {question}

Contexte extrait du site de l'IMT:
{context}

En tant qu'assistant de l'IMT, réponds à la question en utilisant le contexte fourni.
Si l'information n'est pas dans le contexte, indique-le clairement.
Sois précis, utile et professionnel.

Réponse:"""
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retourne des informations sur le système RAG."""
        stats = self.rag_system.get_stats()
        
        return {
            "orchestrator": {
                "mode": self.rag_mode,
                "default_k": self.default_k,
                "status": "active"
            },
            "rag_system": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def switch_mode(self, new_mode: str, **kwargs):
        """Change le mode de fonctionnement du RAG."""
        self.rag_mode = new_mode
        self.rag_system = RAGSystemFactory.create(new_mode, **kwargs)
        logger.info(f"🔄 Mode RAG changé vers: {new_mode}")

# ============================================================================
# SINGLETON ET UTILITAIRES
# ============================================================================

_rag_orchestrator_instance = None

def get_rag_orchestrator(rag_mode: str = "mock", **kwargs) -> RAGOrchestrator:
    """
    Factory pour obtenir une instance unique de l'orchestrateur RAG.
    
    Args:
        rag_mode: Mode de fonctionnement
        **kwargs: Arguments supplémentaires
        
    Returns:
        RAGOrchestrator: Instance de l'orchestrateur
    """
    global _rag_orchestrator_instance
    
    if _rag_orchestrator_instance is None:
        _rag_orchestrator_instance = RAGOrchestrator(rag_mode, **kwargs)
    elif _rag_orchestrator_instance.rag_mode != rag_mode:
        _rag_orchestrator_instance.switch_mode(rag_mode, **kwargs)
    
    return _rag_orchestrator_instance

def format_rag_response_for_llm(rag_response: Dict) -> str:
    """
    Formate la réponse RAG pour l'injection dans un prompt LLM.
    
    Args:
        rag_response: Réponse de l'orchestrateur RAG
        
    Returns:
        str: Contexte formaté pour le LLM
    """
    context = rag_response.get("context", "")
    confidence = rag_response.get("confidence", 0)
    
    header = f"Contexte IMT (confiance: {confidence:.1%}):\n"
    return header + context

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("🧠 Test du RAG Orchestrator...")
    
    # Initialiser avec logging
    logging.basicConfig(level=logging.INFO)
    
    # Test avec mock
    orchestrator = RAGOrchestrator(rag_mode="mock")
    
    # Test de recherche
    test_questions = [
        "Quels sont les frais de scolarité ?",
        "Comment s'inscrire en master ?",
        "Où se trouve le campus ?"
    ]
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        response = orchestrator.answer_with_context(question)
        
        print(f"   ✅ A du contexte: {response['has_context']}")
        print(f"   📊 Confiance: {response['confidence']:.1%}")
        print(f"   📄 Contexte (extrait): {response['context'][:200]}...")
    
    # Informations système
    print("\n📊 Informations système:")
    info = orchestrator.get_system_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Tests RAG orchestrator terminés")