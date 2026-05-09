"""
MarocUGC Studio - Test #2
Prompt engineering avancé : System prompt + Few-shot learning
"""

import ollama

# 1. SYSTEM PROMPT : on définit le RÔLE du modèle
system_prompt = """Tu es un expert en création de contenu UGC viral pour TikTok et Instagram, 
spécialisé dans le marché marocain et la culture darija/française.

RÈGLES STRICTES :
- Le hook doit faire MAXIMUM 12 mots (3 secondes oral)
- Format moderne : POV, Wait until, Personne ne sait que, J'ai testé...
- Ton naturel, comme un ami qui parle, JAMAIS publicitaire
- Pas de hashtags dans le hook (ils viennent après)
- Utiliser le contexte marocain quand c'est pertinent
- INTERDICTION d'inventer des expressions ou mots qui n'existent pas
"""

# 2. FEW-SHOT : on donne 3 exemples concrets de hooks qui cartonnent
few_shot_examples = """
Voici 3 exemples de hooks viraux qui ont marché :

EXEMPLE 1 (produit beauté) :
Hook: "POV: t'as enfin trouvé la crème qui te fait passer pour 18 ans"
Pourquoi ça marche: format POV, promesse claire, ton conversationnel.

EXEMPLE 2 (produit food) :
Hook: "Wait... vous mangez encore le tajine ? Testez ÇA d'abord"
Pourquoi ça marche: pattern interrupt + curiosité + CTA implicite.

EXEMPLE 3 (skincare) :
Hook: "J'ai testé 47 sérums avant de trouver le seul qui marche"
Pourquoi ça marche: chiffre spécifique = crédibilité + storytelling.
"""

# 3. LA REQUÊTE FINALE
user_request = """
Maintenant, génère UN SEUL hook viral pour ce produit :

Produit: Huile d'argan bio marocaine pure
Plateforme: TikTok
Audience: femmes 20-35 ans intéressées par la beauté naturelle

Donne juste le hook, rien d'autre. Pas d'explication, pas d'emojis dans le hook.
"""

# 4. APPEL À LLAMA AVEC LE PROMPT COMPLET
print("🤖 Llama réfléchit (avec exemples)...")

response = ollama.chat(
    model='llama3.2:3b',
    messages=[
        {'role': 'system', 'content': system_prompt + few_shot_examples},
        {'role': 'user', 'content': user_request}
    ]
)

hook = response['message']['content']

print("\n" + "="*50)
print("🎬 HOOK GÉNÉRÉ (V2 — avec prompt engineering) :")
print("="*50)
print(hook)
print("="*50)

