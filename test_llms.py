# test_final_langfuse.py
import asyncio
from brain.chain import get_conversation_chain

async def main():
    print("🎯 TEST FINAL LANGFUSE")
    print("=" * 50)
    
    # 1. Créer une chaîne
    chain = get_conversation_chain("test_final")
    
    # 2. Vérifier le moniteur
    print(f"🔍 Moniteur utilisé: {type(chain.monitor).__name__}")
    print(f"🔍 Langfuse disponible: {getattr(chain.monitor, 'langfuse_available', False)}")
    
    # 3. Faire un appel
    print("\n🤖 Test d'appel LLM...")
    result = await chain.process("Bonjour, peux-tu me parler de l'IMT ?")
    
    print(f"\n✅ Réponse reçue ({len(result['text'])} caractères):")
    print(f"   {result['text'][:150]}...")
    
    # 4. Vérifier si log_llm_response a été appelé
    if hasattr(chain.monitor, 'langfuse') and chain.monitor.langfuse:
        print(f"\n📤 Langfuse object: {chain.monitor.langfuse}")
        print("👉 Va sur https://cloud.langfuse.com et vérifie les traces !")
    else:
        print("\n⚠️ Langfuse non disponible dans le moniteur")

if __name__ == "__main__":
    asyncio.run(main())






    from brain.prompts import PROMPTS

prompt = PROMPTS["email_data_extraction"]
resultat = prompt.format(user_message="Je veux écrire au directeur")

print(resultat)  # Vérifie qu'il n'y a pas d'erreur