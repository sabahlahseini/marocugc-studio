"""
MarocUGC Studio - Agent 5 : Hashtag Optimizer
Mission : générer un mix de hashtags (broad + niche + trending) pour TikTok/Instagram.
"""

import ollama
import re


class HashtagOptimizer:
    """Agent qui génère des hashtags optimisés pour la viralité."""

    def __init__(self, llm_model='llama3.2:3b'):
        self.llm_model = llm_model
        self.system_prompt = """Tu es un expert en stratégie hashtag pour TikTok et Instagram.

RÈGLES STRICTES :
- Génère 12 hashtags répartis en 3 catégories :
  * 4 BROAD (forte audience, mots simples) ex: #beauty #skincare
  * 4 NICHE (audience qualifiée, plus précis) ex: #arganoiltips #moroccanbeauty
  * 4 TRENDING (formats viraux du moment) ex: #grwm #pov #routinebeauty
- Pas d'espace, pas d'accents
- Mix français/anglais selon la pertinence
- INTERDICTION d'inventer des hashtags qui n'existent pas réellement
- Pas de hashtags interdits ou borderline"""

    def generate(self, product, hook=None, category=None):
        """
        Génère un set de hashtags optimisés.

        Args:
            product: description du produit
            hook: le hook validé (pour contexte)
            category: skincare/haircare (pour ciblage)

        Returns:
            dict avec 3 listes (broad, niche, trending) + liste flat
        """
        print(f"\n🏷️  [Agent 5: Hashtag Optimizer] Génération des hashtags...")

        context = f"PRODUIT : {product}\n"
        if category:
            context += f"CATÉGORIE : {category}\n"
        if hook:
            context += f"HOOK : {hook}\n"

        user_prompt = f"""{context}

Génère 12 hashtags optimisés en respectant STRICTEMENT ce format :

BROAD: #hashtag1 #hashtag2 #hashtag3 #hashtag4
NICHE: #hashtag1 #hashtag2 #hashtag3 #hashtag4
TRENDING: #hashtag1 #hashtag2 #hashtag3 #hashtag4

EXEMPLE pour un produit beauté/cheveux :
BROAD: #hair #haircare #beauty #healthy
NICHE: #arganoil #moroccanbeauty #naturalhair #drycarehair
TRENDING: #grwm #hairtok #beautyhack #routinebeauty

Maintenant génère pour ce produit. Pas d'explication, juste les 3 lignes."""

        print("   🤖 Llama génère les hashtags...")
        response = ollama.chat(
            model=self.llm_model,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        )

        raw = response['message']['content']

        # Parser
        hashtags = self._parse(raw)

        # Stats
        all_tags = hashtags['broad'] + hashtags['niche'] + hashtags['trending']
        print(f"   ✅ {len(all_tags)} hashtags générés ({len(hashtags['broad'])} broad, "
              f"{len(hashtags['niche'])} niche, {len(hashtags['trending'])} trending)")

        return {
            'broad': hashtags['broad'],
            'niche': hashtags['niche'],
            'trending': hashtags['trending'],
            'all': all_tags,
            'flat_string': ' '.join(all_tags)
        }

    def _parse(self, raw_text):
        """Parse les 3 catégories de hashtags depuis la sortie."""
        result = {'broad': [], 'niche': [], 'trending': []}

        patterns = {
            'broad': r'BROAD\s*[:\-]\s*(.+?)(?=\n.*?(?:NICHE|TRENDING)|$)',
            'niche': r'NICHE\s*[:\-]\s*(.+?)(?=\n.*?(?:BROAD|TRENDING)|$)',
            'trending': r'TRENDING\s*[:\-]\s*(.+?)(?=\n.*?(?:BROAD|NICHE)|$)'
        }

        for category, pattern in patterns.items():
            match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
            if match:
                line = match.group(1).strip()
                # Extraire tous les #motsclé
                tags = re.findall(r'#\w+', line)
                # Nettoyage : minuscules, pas de doublons
                tags = list(dict.fromkeys([t.lower() for t in tags]))
                result[category] = tags

        # Fallback : si rien parsé, extraire tous les hashtags du texte
        if not (result['broad'] or result['niche'] or result['trending']):
            all_tags = re.findall(r'#\w+', raw_text)
            all_tags = list(dict.fromkeys([t.lower() for t in all_tags]))
            # Diviser arbitrairement en 3 groupes
            n = len(all_tags) // 3
            result['broad'] = all_tags[:n] if n > 0 else []
            result['niche'] = all_tags[n:2*n] if n > 0 else []
            result['trending'] = all_tags[2*n:] if n > 0 else []

        return result


# Test direct
if __name__ == "__main__":
    optimizer = HashtagOptimizer()

    product = "Huile d'argan bio marocaine pour cheveux secs"
    hook = "J'ai découvert mon secret pour des cheveux brillants"

    result = optimizer.generate(product=product, hook=hook, category="haircare")

    print("\n" + "="*60)
    print(f"🏷️  HASHTAGS pour : {product}")
    print("="*60)
    print(f"\n📢 BROAD     : {' '.join(result['broad'])}")
    print(f"🎯 NICHE     : {' '.join(result['niche'])}")
    print(f"🔥 TRENDING  : {' '.join(result['trending'])}")
    print(f"\n📋 ALL ({len(result['all'])}) : {result['flat_string']}")
    print("="*60)