"""
MarocUGC Studio - Agent 3 : Hook Critic
Mission : évaluer les hooks candidats et choisir le meilleur.
"""

import ollama
import re


class HookCritic:
    """Agent qui évalue et sélectionne le meilleur hook parmi des candidats."""
    
    MAX_WORDS = 12
    MIN_WORDS = 5
    
    # Mots/patterns suspects qui indiquent une hallucination
    SUSPICIOUS_PATTERNS = [
        r'\blaissant\b',  # mot incohérent vu en V2
        r'\bplus répétées\b',
        r'\bronge mon larynx\b',  # le classique de notre V1
    ]
    
    def __init__(self, llm_model='llama3.2:3b'):
        self.llm_model = llm_model
    
    
    def evaluate_rule_based(self, hook):
        """
        Évaluation rule-based : applique des règles dures.
        Retourne un dict avec score + détails.
        """
        word_count = len(hook.split())
        issues = []
        score = 100
        
        # Règle 1 : longueur
        if word_count > self.MAX_WORDS:
            penalty = (word_count - self.MAX_WORDS) * 10
            score -= penalty
            issues.append(f"Trop long ({word_count} mots, max {self.MAX_WORDS})")
        elif word_count < self.MIN_WORDS:
            score -= 30
            issues.append(f"Trop court ({word_count} mots)")
        
        # Règle 2 : hallucinations détectables par regex
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, hook.lower()):
                score -= 50
                issues.append(f"Mot/expression suspect détecté")
                break
        
        # Règle 3 : longueur minimum sanity check
        if len(hook) < 10:
            score -= 40
            issues.append("Hook trop court (caractères)")
        
        return {
            'hook': hook,
            'word_count': word_count,
            'rule_based_score': max(0, score),
            'issues': issues
        }
    
    
    def select_best(self, hooks, product):
        """
        Évalue tous les hooks et retourne le meilleur avec son analyse.
        
        Args:
            hooks: liste de hooks candidats
            product: description du produit
        
        Returns:
            dict avec le meilleur hook + breakdown
        """
        print(f"\n🧐 [Agent 3: Hook Critic] Évaluation de {len(hooks)} hooks...")
        
        # 1. Évaluation rule-based
        evaluations = [self.evaluate_rule_based(h) for h in hooks]
        
        # 2. Affichage des évaluations
        print("\n   Scores rule-based :")
        for i, ev in enumerate(evaluations, 1):
            status = "✅" if ev['rule_based_score'] >= 70 else "⚠️" if ev['rule_based_score'] >= 40 else "❌"
            print(f"   {status} Hook #{i} ({ev['word_count']} mots, score: {ev['rule_based_score']}/100)")
            if ev['issues']:
                print(f"      Issues: {', '.join(ev['issues'])}")
        
        # 3. Filtrer les hooks acceptables (score >= 40)
        acceptable = [ev for ev in evaluations if ev['rule_based_score'] >= 40]
        
        if not acceptable:
            print("   🚨 Aucun hook acceptable → utilisation du moins mauvais")
            best = max(evaluations, key=lambda x: x['rule_based_score'])
            return {
                'best_hook': best['hook'],
                'score': best['rule_based_score'],
                'all_evaluations': evaluations,
                'warning': "Tous les hooks ont des problèmes. Régénération recommandée."
            }
        
        # 4. Si plusieurs sont OK, demander au LLM de choisir
        if len(acceptable) > 1:
            best = self._llm_pick_best(acceptable, product)
        else:
            best = acceptable[0]
        
        print(f"\n   🏆 MEILLEUR HOOK : {best['hook']}")
        
        return {
            'best_hook': best['hook'],
            'score': best['rule_based_score'],
            'all_evaluations': evaluations,
            'warning': None
        }
    
    
    def _llm_pick_best(self, candidates, product):
        """Demande au LLM de choisir le meilleur parmi les candidats acceptables."""
        candidates_text = "\n".join([
            f"{i+1}. {c['hook']}"
            for i, c in enumerate(candidates)
        ])
        
        prompt = f"""Voici plusieurs hooks viraux candidats pour ce produit : {product}

CANDIDATS :
{candidates_text}

Quel est le MEILLEUR hook ? Critères :
- Le plus accrocheur (3 premières secondes décisives)
- Le plus naturel (pas publicitaire)
- Le plus pertinent pour le produit
- Le pattern le plus viral (POV, Wait, etc.)

Réponds UNIQUEMENT par le numéro (1, 2, 3...). Pas d'explication."""
        
        response = ollama.chat(
            model=self.llm_model,
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        # Parser le numéro
        match = re.search(r'\d+', response['message']['content'])
        if match:
            idx = int(match.group()) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]
        
        # Fallback : meilleur score rule-based
        return max(candidates, key=lambda x: x['rule_based_score'])


# Test direct
if __name__ == "__main__":
    from rag.retrieval import UGCRetriever
    from agents.trend_analyst import TrendAnalyst
    from agents.hook_generator import HookGenerator
    
    retriever = UGCRetriever()
    analyst = TrendAnalyst(retriever)
    generator = HookGenerator()
    critic = HookCritic()
    
    product = "Huile d'argan bio marocaine pour cheveux secs"
    
    # Pipeline complet
    analysis_result = analyst.analyze(product)
    hooks = generator.generate(
        product=product,
        analysis=analysis_result['analysis'],
        retrieved_ugc=analysis_result['retrieved_ugc']
    )
    final = critic.select_best(hooks, product)
    
    print("\n" + "="*60)
    print(f"🎬 RÉSULTAT FINAL pour : {product}")
    print("="*60)
    print(f"🏆 HOOK : {final['best_hook']}")
    print(f"📊 SCORE : {final['score']}/100")
    if final['warning']:
        print(f"⚠️  WARNING : {final['warning']}")
    print("="*60)