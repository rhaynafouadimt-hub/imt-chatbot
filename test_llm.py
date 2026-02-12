# test_monitor.py
from brain.monitoring import get_monitor

print('🔍 Test de la factory get_monitor()')
print('=' * 50)

print('\n1. Sans paramètre (doit utiliser config):')
monitor1 = get_monitor('session1')
print(f'   Type: {type(monitor1).__name__}')
print(f'   langfuse_available: {getattr(monitor1, "langfuse_available", "N/A")}')

print('\n2. Avec use_langfuse=True (forcé):')
monitor2 = get_monitor('session2', use_langfuse=True)
print(f'   Type: {type(monitor2).__name__}')
print(f'   langfuse_available: {getattr(monitor2, "langfuse_available", "N/A")}')

# Test supplémentaire : Vérifier les attributs
print('\n3. Attributs du monitor 2:')
if hasattr(monitor2, 'langfuse'):
    print(f'   langfuse: {monitor2.langfuse}')
if hasattr(monitor2, 'langfuse_available'):
    print(f'   langfuse_available: {monitor2.langfuse_available}')
if hasattr(monitor2, '__class__'):
    print(f'   Classe: {monitor2.__class__.__name__}')