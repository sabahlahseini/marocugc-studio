"""
MarocUGC Studio - Agent 2 : Hook Generator
Mission : générer 5 hooks candidats à partir de l'analyse du Trend Analyst.
"""

import ollama
import re


class HookGenerator:
    """Agent qui génère plusieurs hooks candidats selon les patterns recommandés."""
    
    def __init__(self, llm_model='llama3.2:3b'):
        self.llm_model = llm_model
        self.system_prompt = """Tu es un expert en création de hooks viraux pour TikTok et Instagram.

RÈGLES STRICTES :
- Chaque hook fait MAXIMUM 12 mots
- Ton naturel, conversationnel (jamais publicitaire)
- Pas de hashtags, pas d'emojis dans le hook
- Le hook doit clairement parler du PRODUIT donné
- INTERDICTION d'inventer des mots ou expressions
- Tu DOIS respecter le pattern demandé"""
    
    
    def generate(self, product, analysis, retrieved_ugc):
        """
        Génère 5 hooks candidats.
        
        Args:
            product: description du produit
            analysis: output JSON de l'Agent 1
            retrieved_ugc: liste des UGC trouvés par le RAG
        
        Returns:
            liste de 5 hooks (strings)
        """
        print(f"\n✍️  [Agent 2: Hook Generator] Génération de 5 hooks pour '{product}'...")
        
        # Préparer un mini-corpus d'inspiration : juste les hooks (pas les scripts)
        examples = "\n".join([
            f"- [{ugc['format_type']}] {ugc['hook']}"
            for ugc in retrieved_ugc[:3]  # juste les 3 meilleurs
        ])
        
        # Récupérer les patterns recommandés par Agent 1
        patterns = analysis.get('recommended_patterns', [])
        if patterns:
            patterns_text = "\n".join([
                f"- {p.get('pattern', 'unknown')} : {p.get('reason', '')}"
                for p in patterns
            ])
        else:
            patterns_text = "- POV\n- Wait\n- Numbered_Story"
        
        # Récupérer les angles clés
        angles = analysis.get('key_angles', [])
        angles_text = ", ".join(angles) if angles else "à toi de trouver"
        
        # Prompt de génération
        user_prompt = f"""PRODUIT : {product}

PATTERNS À UTILISER (recommandés par notre analyste) :
{patterns_text}

ANGLES CLÉS DU PRODUIT :
{angles_text}

EXEMPLES DE HOOKS VIRAUX (pour t'inspirer du STYLE, pas du contenu) :
{examples}

⚠️ Génère 5 hooks DIFFÉRENTS pour ce produit, en utilisant des patterns variés.

FORMAT DE SORTIE (strict) :
1. [premier hook ici]
2. [deuxième hook ici]
3. [troisième hook ici]
4. [quatrième hook ici]
5. [cinquième hook ici]

Pas d'explication. Juste les 5 hooks numérotés."""
        
        print("   🤖 LLM génère les 5 candidats...")
        response = ollama.chat(
            model=self.llm_model,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        )
        
        raw_output = response['message']['content']
        
        # Parser les hooks numérotés
        hooks = self._parse_hooks(raw_output)
        
        print(f"   ✅ {len(hooks)} hooks générés")
        
        return hooks
    
    
    def _parse_hooks(self, text):
        """Parse le texte numéroté pour extraire les hooks."""
        hooks = []
        # Cherche les lignes du type "1. ...", "2. ..." etc.
        pattern = r'^\s*\d+\.\s*(.+?)$'
        for line in text.strip().split('\n'):
            match = re.match(pattern, line)
            if match:
                hook = match.group(1).strip()
                # Nettoie les guillemets et crochets éventuels
                hook = hook.strip('"\'[]')
                if hook:
                    hooks.append(hook)
        return hooks


# Test direct
if __name__ == "__main__":
    from rag.retrieval import UGCRetriever
    from agents.trend_analyst import TrendAnalyst
    
    retriever = UGCRetriever()
    analyst = TrendAnalyst(retriever)
    generator = HookGenerator()
    
    product = "Huile d'argan bio marocaine pour cheveux secs"
    
    # Étape 1 : Trend Analyst
    analysis_result = analyst.analyze(product)
    
    # Étape 2 : Hook Generator
    hooks = generator.generate(
        product=product,
        analysis=analysis_result['analysis'],
        retrieved_ugc=analysis_result['retrieved_ugc']
    )
    
    print("\n" + "="*60)
    print(f"🎬 5 HOOKS GÉNÉRÉS pour : {product}")
    print("="*60)
    for i, hook in enumerate(hooks, 1):
        print(f"\n  Hook #{i} ({len(hook.split())} mots) :")
        print(f"    → {hook}")
    print("\n" + "="*60)