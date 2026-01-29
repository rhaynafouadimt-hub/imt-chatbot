"""
Utilitaires généraux pour le chatbot IMT.
Fonctions réutilisables, helpers, formatters.
"""

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
import time
import logging
from functools import wraps
import random
import string
from .config import config


logger = logging.getLogger(__name__)

# ============================================================================
# FONCTIONS DE MANIPULATION DE TEXTE
# ============================================================================

def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Nettoie un texte: espaces, sauts de ligne, caractères spéciaux.
    
    Args:
        text: Texte à nettoyer
        max_length: Tronquer à cette longueur si spécifié
        
    Returns:
        str: Texte nettoyé
    """
    if not text:
        return ""
    
    # Supprimer les caractères de contrôle
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Normaliser les espaces et sauts de ligne
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    
    # Supprimer les espaces en début/fin
    cleaned = cleaned.strip()
    
    # Tronquer si nécessaire
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit(' ', 1)[0] + '...'
    
    return cleaned

def extract_json_from_text(text: str) -> Optional[Dict]:
    """
    Extrait un objet JSON d'un texte.
    
    Args:
        text: Texte pouvant contenir du JSON
        
    Returns:
        Optional[Dict]: Objet JSON extrait ou None
    """
    try:
        # Chercher du JSON dans le texte
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            # Essayer chaque match
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Si pas trouvé, essayer de parser tout le texte
        return json.loads(text)
        
    except (json.JSONDecodeError, TypeError):
        return None

def truncate_text(text: str, max_words: int = 100) -> str:
    """
    Tronque un texte à un nombre maximum de mots.
    
    Args:
        text: Texte à tronquer
        max_words: Nombre maximum de mots
        
    Returns:
        str: Texte tronqué
    """
    words = text.split()
    if len(words) <= max_words:
        return text
    
    truncated = ' '.join(words[:max_words])
    if not truncated.endswith(('.', '!', '?')):
        truncated += '...'
    
    return truncated

def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Génère un ID unique.
    
    Args:
        prefix: Préfixe pour l'ID
        length: Longueur de la partie aléatoire
        
    Returns:
        str: ID généré
    """
    timestamp = int(time.time() * 1000)
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_str}"
    return f"{timestamp}_{random_str}"

def calculate_text_hash(text: str) -> str:
    """
    Calcule un hash MD5 d'un texte.
    Utile pour la déduplication.
    
    Args:
        text: Texte à hasher
        
    Returns:
        str: Hash MD5
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# ============================================================================
# FONCTIONS DE FORMATAGE
# ============================================================================

def format_timestamp(timestamp: Optional[Union[datetime, str, float]] = None, 
                    format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formate un timestamp en chaîne lisible.
    
    Args:
        timestamp: Timestamp à formater (datetime, str ISO, ou float)
        format_str: Format de sortie
        
    Returns:
        str: Timestamp formaté
    """
    if timestamp is None:
        dt = datetime.now()
    elif isinstance(timestamp, datetime):
        dt = timestamp
    elif isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            dt = datetime.now()
    elif isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = datetime.now()
    
    return dt.strftime(format_str)

def format_duration(seconds: float) -> str:
    """
    Formate une durée en chaîne lisible.
    
    Args:
        seconds: Durée en secondes
        
    Returns:
        str: Durée formatée
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:.0f}m {secs:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"

def format_file_size(bytes_size: int) -> str:
    """
    Formate une taille de fichier en chaîne lisible.
    
    Args:
        bytes_size: Taille en octets
        
    Returns:
        str: Taille formatée
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024 or unit == 'GB':
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024

# ============================================================================
# FONCTIONS DE VALIDATION
# ============================================================================

def is_valid_email(email: str) -> bool:
    """
    Valide une adresse email.
    
    Args:
        email: Adresse email à valider
        
    Returns:
        bool: True si l'email est valide
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_url(url: str) -> bool:
    """
    Valide une URL.
    
    Args:
        url: URL à valider
        
    Returns:
        bool: True si l'URL est valide
    """
    pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    return re.match(pattern, url) is not None

def validate_required_fields(data: Dict, required_fields: List[str]) -> List[str]:
    """
    Valide que les champs requis sont présents dans un dictionnaire.
    
    Args:
        data: Dictionnaire à valider
        required_fields: Liste des champs requis
        
    Returns:
        List[str]: Liste des champs manquants (vide si tous présents)
    """
    missing = []
    for field in required_fields:
        if field not in data or data[field] in (None, "", []):
            missing.append(field)
    return missing

# ============================================================================
# DÉCORATEURS UTILES
# ============================================================================

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, 
                    backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Décorateur pour réessayer une fonction en cas d'échec.
    
    Args:
        max_attempts: Nombre maximum de tentatives
        delay: Délai initial entre les tentatives
        backoff: Facteur de multiplication du délai
        exceptions: Exceptions à catcher
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        break
                    
                    logger.warning(f"⚠️ Tentative {attempt + 1}/{max_attempts} échouée: {e}")
                    logger.info(f"⏳ Nouvelle tentative dans {current_delay:.1f}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            logger.error(f"❌ Échec après {max_attempts} tentatives: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator

def timing_decorator(func: Callable):
    """
    Décorateur pour mesurer le temps d'exécution.
    
    Args:
        func: Fonction à décorer
        
    Returns:
        Callable: Fonction décorée
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.debug(f"⏱️ {func.__name__} exécuté en {(end_time - start_time)*1000:.2f}ms")
        return result
    
    return wrapper

def log_execution(func: Callable):
    """
    Décorateur pour logger l'exécution d'une fonction.
    
    Args:
        func: Fonction à décorer
        
    Returns:
        Callable: Fonction décorée
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"▶️ Début {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"✅ Fin {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"❌ Erreur dans {func.__name__}: {e}")
            raise
    
    return wrapper

# =========================== SUGESTION DEEP
# Ajouter dans la section "DÉCORATEURS UTILES"

def llm_api_decorator(func: Callable):
    """
    Décorateur spécialisé pour les appels API LLM.
    Log les métriques importantes: tokens, modèle, latence.
    """
    @wraps(func)
    @retry_on_failure(max_attempts=3, delay=0.5, backoff=2.0)
    @timing_decorator
    def wrapper(*args, **kwargs):
        
        # Extraire les infos pertinentes des kwargs
        model = kwargs.get('model') or config.get_llm_model_name()
        temperature = kwargs.get('temperature', config.llm.TEMPERATURE)
        
        logger.info(f"🤖 Appel LLM: modèle={model}, temp={temperature}")
        
        try:
            result = func(*args, **kwargs)
            
            # Log supplémentaire si la réponse contient des infos de tokens
            if hasattr(result, 'usage'):
                usage = result.usage
                logger.info(
                    f"📊 Tokens utilisés: prompt={getattr(usage, 'prompt_tokens', 'N/A')}, "
                    f"completion={getattr(usage, 'completion_tokens', 'N/A')}, "
                    f"total={getattr(usage, 'total_tokens', 'N/A')}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur API LLM ({model}): {e}")
            # Tu pourrais ajouter une métrique spécifique ici (ex: incrementer un compteur d'erreurs)
            raise
    
    return wrapper


def trace_langfuse(func: Callable):
    """
    Décorateur pour tracer automatiquement avec Langfuse.
    À utiliser si Langfuse est activé dans la config.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from .config import config
        
        # Vérifier si Langfuse est activé
        if not config.monitoring.ENABLED or not config.monitoring.USE_LANGFUSE:
            return func(*args, **kwargs)
        
        try:
            # Importer conditionnellement
            from langfuse import Langfuse
            langfuse = Langfuse(
                secret_key=config.monitoring.LANGFUSE_SECRET_KEY,
                public_key=config.monitoring.LANGFUSE_PUBLIC_KEY,
                host=config.monitoring.LANGFUSE_HOST
            )
            
            # Créer une trace
            trace = langfuse.trace(
                name=f"utils.{func.__name__}",
                metadata={
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
            )
            
            # Exécuter avec un span
            with trace.span(name=func.__name__) as span:
                result = func(*args, **kwargs)
                span.output = {"success": True, "result_type": type(result).__name__}
                return result
                
        except ImportError:
            logger.warning("Langfuse non installé, tracing ignoré")
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Erreur tracing Langfuse: {e}")
            return func(*args, **kwargs)
    
    return wrapper

# ============================================================================
# FONCTIONS DE CONVERSION
# ============================================================================

def safe_json_dumps(data: Any, indent: Optional[int] = 2) -> str:
    """
    Convertit des données en JSON de manière sûre.
    Gère les objets datetime et autres types non sérialisables.
    
    Args:
        data: Données à sérialiser
        indent: Indentation JSON
        
    Returns:
        str: JSON sérialisé
    """
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        else:
            return str(obj)
    
    return json.dumps(data, indent=indent, default=default_serializer, ensure_ascii=False)

def dict_to_query_params(params: Dict) -> str:
    """
    Convertit un dictionnaire en paramètres de requête URL.
    
    Args:
        params: Dictionnaire de paramètres
        
    Returns:
        str: Chaîne de paramètres URL
    """
    return '&'.join([f"{key}={value}" for key, value in params.items() if value is not None])

def flatten_dict(nested_dict: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Aplatit un dictionnaire nested.
    
    Args:
        nested_dict: Dictionnaire nested
        parent_key: Clé parente (interne)
        sep: Séparateur de clés
        
    Returns:
        Dict: Dictionnaire aplati
    """
    items = []
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    
    return dict(items)

# ============================================================================
# Fonction de persistance pour Redis
# ============================================================================

def serialize_for_redis(data: Any, compress: bool = False) -> str:
    """
    Sérialise des données pour le stockage Redis.
    
    Args:
        data: Données à sérialiser
        compress: Activer la compression gzip (pour les gros objets)
        
    Returns:
        str: Données sérialisées (JSON string ou JSON+gzip)
    """
    import gzip
    import base64
    
    # Sérialiser en JSON
    json_str = safe_json_dumps(data, indent=None)
    
    if compress:
        # Compresser
        compressed = gzip.compress(json_str.encode('utf-8'))
        # Encoder en base64 pour stockage texte
        return base64.b64encode(compressed).decode('utf-8')
    
    return json_str


def deserialize_from_redis(redis_data: str, compressed: bool = False) -> Any:
    """
    Désérialise des données depuis Redis.
    
    Args:
        redis_data: Données depuis Redis
        compressed: Les données sont-elles compressées?
        
    Returns:
        Any: Données désérialisées
    """
    import gzip
    import base64
    import json
    
    try:
        if compressed:
            # Décompresser
            decoded = base64.b64decode(redis_data.encode('utf-8'))
            json_str = gzip.decompress(decoded).decode('utf-8')
        else:
            json_str = redis_data
        
        return json.loads(json_str)
        
    except Exception as e:
        logger.error(f"Erreur désérialisation Redis: {e}")
        raise ValueError(f"Données Redis invalides: {e}")


def redis_key_builder(namespace: str, *parts) -> str:
    """
    Construit une clé Redis structurée.
    
    Args:
        namespace: Namespace (ex: "imt_chatbot")
        *parts: Partie(s) de la clé
        
    Returns:
        str: Clé Redis complète
    """
    
    # Utiliser le préfixe de la config si disponible
    prefix = config.memory.REDIS_PREFIX if hasattr(config, 'memory') else namespace
    
    # Nettoyer les parties
    cleaned_parts = [str(part).strip().replace(':', '_') for part in parts if part]
    
    # Construire la clé
    key_parts = [prefix] + cleaned_parts
    return ":".join(key_parts)

# ============================================================================
# FONCTIONS DE MANIPULATION DE LISTE/DICT
# ============================================================================

def merge_dicts(dict1: Dict, dict2: Dict, overwrite: bool = True) -> Dict:
    """
    Fusionne deux dictionnaires.
    
    Args:
        dict1: Premier dictionnaire
        dict2: Deuxième dictionnaire
        overwrite: Écraser les clés existantes si True
        
    Returns:
        Dict: Dictionnaire fusionné
    """
    if overwrite:
        return {**dict1, **dict2}
    else:
        return {**dict2, **dict1}

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Divise une liste en chunks de taille fixe.
    
    Args:
        lst: Liste à diviser
        chunk_size: Taille de chaque chunk
        
    Returns:
        List[List]: Liste de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def get_nested_value(data: Dict, key_path: str, default: Any = None) -> Any:
    """
    Récupère une valeur nested dans un dictionnaire.
    
    Args:
        data: Dictionnaire source
        key_path: Chemin de la clé (ex: "user.profile.name")
        default: Valeur par défaut si non trouvé
        
    Returns:
        Any: Valeur trouvée ou default
    """
    keys = key_path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current

# ============================================================================
# FONCTIONS SPÉCIFIQUES IMT
# ============================================================================

def extract_imt_info(text: str) -> Dict[str, str]:
    """
    Extrait les informations spécifiques à l'IMT d'un texte.
    
    Args:
        text: Texte à analyser
        
    Returns:
        Dict: Informations extraites
    """
    info = {}
    
    # Extraire les numéros de téléphone
    phone_pattern = r'(\+?\d[\d\s\-\(\)]{7,}\d)'
    phones = re.findall(phone_pattern, text)
    if phones:
        info['phones'] = phones
    
    # Extraire les emails
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = re.findall(email_pattern, text)
    if emails:
        info['emails'] = emails
    
    # Extraire les montants (frais)
    amount_pattern = r'(\d[\d\s,]*\.?\d*)\s*(FCFA|€|\$|USD)'
    amounts = re.findall(amount_pattern, text)
    if amounts:
        info['amounts'] = [f"{amt[0]} {amt[1]}" for amt in amounts]
    
    return info

def format_imt_response(text: str) -> str:
    """
    Formate une réponse pour qu'elle soit adaptée à l'IMT.
    
    Args:
        text: Réponse à formater
        
    Returns:
        str: Réponse formatée
    """
    # Ajouter une signature si absente
    if "IMT" not in text.upper() and "Institut" not in text:
        text += "\n\n---\n*Assistant IMT - Institut Management et Technologie Sénégal*"
    
    return text

# ============================================================================
# Suggestion faites par Deep

def format_with_project(message: str, include_version: bool = False) -> str:
    """
    Formate un message avec le nom du projet IMT.
    
    Args:
        message: Message à formater
        include_version: Inclure la version du projet
        
    Returns:
        str: Message formaté
    """
    project_info = config.PROJECT_NAME
    if include_version:
        project_info = f"{project_info} v{config.VERSION}"
    
    return f"[{project_info}] {message}"


def get_project_header() -> Dict[str, str]:
    """
    Retourne un en-tête standard avec les infos du projet.
    Utile pour les logs structurés ou les traces.
    
    Returns:
        Dict: En-tête avec infos projet
    """
    return {
        "project": config.PROJECT_NAME,
        "version": config.VERSION,
        "environment": config.ENVIRONMENT,
        "timestamp": format_timestamp()
    }

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("🧪 Test des utilitaires...")
    
    # Test clean_text
    dirty_text = "  Hello   World  \n\nTest  "
    cleaned = clean_text(dirty_text)
    print(f"✅ clean_text: '{dirty_text}' -> '{cleaned}'")
    
    # Test extract_json_from_text
    text_with_json = 'Some text {"name": "John", "age": 30} more text'
    extracted = extract_json_from_text(text_with_json)
    print(f"✅ extract_json: {extracted}")
    
    # Test format_timestamp
    formatted = format_timestamp()
    print(f"✅ format_timestamp: {formatted}")
    
    # Test is_valid_email
    print(f"✅ is_valid_email('test@imt.sn'): {is_valid_email('test@imt.sn')}")
    
    # Test generate_id
    id1 = generate_id("session")
    id2 = generate_id("session")
    print(f"✅ generate_id: {id1}, {id2} (différents: {id1 != id2})")
    
    # Test chunk_list
    my_list = [1, 2, 3, 4, 5, 6, 7]
    chunks = chunk_list(my_list, 3)
    print(f"✅ chunk_list: {my_list} -> {chunks}")
    
    print("\n✅ Tests utilitaires terminés")