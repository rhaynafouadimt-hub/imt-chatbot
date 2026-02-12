# list_models.py
import os
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# Charger la clé API
load_dotenv(Path(__file__).parent / '.env')
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY non trouvée")

# Configurer l'API
genai.configure(api_key=api_key)

print("🔍 LISTE DES MODÈLES GEMINI DISPONIBLES (2026)")
print("=" * 60)

try:
    # Lister tous les modèles
    models = genai.list_models()
    
    print(f"📊 Nombre total de modèles: {len(list(models))}")
    print("\n🎯 Modèles supportant generateContent (pour chat):")
    print("-" * 40)
    
    supported_models = []
    
    for model in models:
        model_info = genai.get_model(model.name)
        
        # Filtrer les modèles Gemini qui supportent generateContent
        if 'generateContent' in model_info.supported_generation_methods:
            if 'gemini' in model.name.lower():
                supported_models.append(model.name)
                
                # Afficher les infos
                print(f"\n✨ {model.name}")
                print(f"   Description: {model.description}")
                print(f"   Token limit: {getattr(model_info, 'input_token_limit', 'N/A')}")
                print(f"   Méthodes supportées: {', '.join(model_info.supported_generation_methods)}")
    
    print("\n" + "=" * 60)
    print("📋 MODÈLES RECOMMANDÉS:")
    for model in supported_models:
        print(f"  - {model}")
    
    if supported_models:
        # Suggérer le meilleur modèle
        latest_models = [m for m in supported_models if '2.0' in m or '2026' in m or 'ultra' in m]
        if latest_models:
            recommended = latest_models[0]
        else:
            recommended = supported_models[-1]  # Le dernier de la liste
        
        print(f"\n💡 MODÈLE SUGGÉRÉ POUR VOTRE APPLICATION: {recommended}")
        
        # Créer un fichier de config
        with open('gemini_models_2026.txt', 'w') as f:
            f.write("# Modèles Gemini disponibles en 2026\n")
            f.write("# Généré automatiquement\n\n")
            for model in supported_models:
                f.write(f"{model}\n")
        
        print(f"📝 Liste sauvegardée dans: gemini_models_2026.txt")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("\n🔄 Essai d'une méthode alternative...")
    
    # Essayer avec des modèles connus en 2026
    likely_models_2026 = [
        "gemini-2.0-ultra",
        "gemini-2.0-pro", 
        "gemini-2.0-flash",
        "gemini-1.5-ultra",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-advision-2.0",  # Pour la vision peut-être
        "gemini-code-2.0",      # Pour le code
    ]
    
    print("\n🔮 Modèles probables en 2026:")
    for model in likely_models_2026:
        print(f"  - {model}")
    
    print("\n💡 Essayez ces modèles dans votre configuration.")