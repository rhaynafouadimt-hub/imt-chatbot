# test_final_langfuse.py
import asyncio
from brain.chain import get_conversation_chain
from brain.config import config

async def test():
    session_id = "test_final_success"
    print(f"🎯 Session: {session_id}")
    
    chain = get_conversation_chain(session_id)
    
    print(f"\n🔍 Moniteur: {type(chain.monitor).__name__}")
    print(f"🔍 Langfuse actif: {getattr(chain.monitor, 'langfuse_available', False)}")
    print(f"🔍 Modèle configuré: {config.get_llm_model_name()}")
    
    # Test simple
    print("\n🤖 Envoi d'une requête...")
    result = await chain.process("Bonjour, présente-toi")
    print(f"✅ Réponse: {result['text'][:80]}...")
    
    print(f"\n📤 Vérifie sur https://cloud.langfuse.com")
    print(f"   Session: {session_id}")
    print(f"   Modèle: {config.get_llm_model_name()}")

if __name__ == "__main__":
    asyncio.run(test())