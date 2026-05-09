"""
MarocUGC Studio - Test #1
Premier appel à Llama 3.2 via Ollama
"""

import ollama

# 1. Le prompt qu'on envoie à Llama
prompt = """Génère un hook TikTok viral de 3 secondes maximum 
pour de l'huile d'argan marocaine bio. 
Style: court, punchy, format UGC moderne (POV, Wait until..., I tried...).
Réponds en français.
Donne une seule proposition, pas de liste."""

# 2. Appel au modèle
print("🤖 Llama réfléchit...")
response = ollama.chat(
    model='llama3.2:3b',
    messages=[
        {'role': 'user', 'content': prompt}
    ]
)

# 3. Récupérer et afficher la réponse
hook = response['message']['content']

print("\n" + "="*50)
print("🎬 HOOK GÉNÉRÉ :")
print("="*50)
print(hook)
print("="*50)