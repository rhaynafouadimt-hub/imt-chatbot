# rag_imt.py
import warnings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# Supprimer le warning Pydantic pour Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning)

# Créer les embeddings (une seule fois)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Charger le vectorstore FAISS existant
try:
    vectorstore = FAISS.load_local(
        "imt_faiss",
        embeddings,
        allow_dangerous_deserialization=True
    )
    print("✅ Vectorstore chargé avec succès.")
except Exception as e:
    print("❌ Erreur lors du chargement du vectorstore :", e)
    vectorstore = None


def ask_imt(question: str) -> str:
    """
    Pose une question et retourne la réponse basée sur l'index FAISS.
    """
    if vectorstore is None:
        return "Le vectorstore n'a pas pu être chargé."
    
    print(f"🔎 Recherche pour la question : {question}")
    
    try:
        docs = vectorstore.similarity_search(question, k=3)
    except Exception as e:
        return f"Erreur pendant la recherche : {e}"
    
    if not docs:
        return "Je n'ai pas trouvé d'information à ce sujet."
    
    response = "📚 Réponse basée sur les données IMT :\n\n"
    for i, doc in enumerate(docs, 1):
        response += f"{i}. {doc.page_content}\n\n"
    
    return response


def search_imt(query: str, k: int = 3) -> list[dict]:
    """
    Recherche et retourne les documents avec métadonnées.
    """
    if vectorstore is None:
        return []
    
    docs = vectorstore.similarity_search(query, k=k)
    
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "inconnu"),
        }
        for doc in docs
    ]
