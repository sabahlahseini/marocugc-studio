"""
MarocUGC Studio - Agent 4 : Script Writer (V2 — robuste)
"""

import ollama
import re


class ScriptWriter:
    """Agent qui transforme un hook en script complet structuré."""

    def __init__(self, llm_model='llama3.2:3b'):
        self.llm_model = llm_model
        self.system_prompt = """Tu es un expert en écriture de scripts UGC pour TikTok.

RÈGLES STRICTES :
- Tu DOIS respecter le format de sortie exact (HOOK:, PROBLÈME:, SOLUTION:, CTA:)
- Durée totale : 25-30 secondes (~70-90 mots)
- Ton 100% naturel, comme une amie qui parle à une autre
- Pas de langage publicitaire, pas de superlatifs forcés
- INTERDICTION d'inventer des produits, ingrédients, ou faits"""

    def write(self, hook, product, retrieved_ugc=None):
        """Génère un script complet à partir d'un hook validé."""
        print(f"\n📝 [Agent 4: Script Writer] Génération du script complet...")

        user_prompt = f"""HOOK À UTILISER : "{hook}"
PRODUIT : {product}

Écris un script UGC complet de 25-30 secondes en RESPECTANT EXACTEMENT ce format :

HOOK: {hook}
PROBLÈME: [1-2 phrases sur le problème que résout le produit]
SOLUTION: [2-3 phrases présentant le produit et ses bénéfices]
CTA: [1 phrase d'appel à l'action — lien en bio, code promo, etc.]

EXEMPLE DE SORTIE CORRECTE (à imiter exactement) :
HOOK: J'ai testé 47 huiles capillaires avant de trouver LA bonne
PROBLÈME: Mes cheveux étaient secs, cassants, sans vie depuis des années.
SOLUTION: Cette huile d'argan pure m'a tout changé. En 3 semaines, mes cheveux sont devenus brillants, doux, plus de pointes fourchues.
CTA: Code promo SECRET15 dans la bio pour -15% sur ton premier achat.

Maintenant à toi. Réponds en respectant STRICTEMENT le format avec les 4 labels."""

        print("   🤖 Llama écrit le script...")
        response = ollama.chat(
            model=self.llm_model,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        )

        raw_script = response['message']['content']

        # DEBUG (commenté pour la prod, à décommenter si besoin)
        # print("\n--- DEBUG ---")
        # print(raw_script)
        # print("--- Fin DEBUG ---\n")

        # Tenter le parsing strict d'abord
        script_dict = self._parse_strict(raw_script, hook)

        # Si le parsing strict a échoué (champs vides), utiliser le fallback intelligent
        if not script_dict['probleme'] or not script_dict['solution']:
            print("   ⚠️  Format strict non respecté, fallback intelligent activé")
            script_dict = self._parse_fallback(raw_script, hook)

        full_text = f"{script_dict['hook']} {script_dict['probleme']} {script_dict['solution']} {script_dict['cta']}"
        word_count = len(full_text.split())

        print(f"   ✅ Script généré ({word_count} mots, ~{word_count // 3} sec oral)")

        return {
            'structured': script_dict,
            'full_text': full_text.strip(),
            'word_count': word_count,
            'estimated_seconds': word_count // 3
        }

    def _parse_strict(self, raw_text, fallback_hook):
        """Parse en cherchant les labels HOOK:/PROBLÈME:/SOLUTION:/CTA:"""
        result = {
            'hook': fallback_hook,
            'probleme': '',
            'solution': '',
            'cta': ''
        }

        patterns = {
            'hook': r'(?:\*+\s*)?HOOK\s*\*?\s*[:\-]\s*(.+?)(?=(?:\n\s*(?:\*+\s*)?(?:PROBL[EÈ]ME|SOLUTION|CTA))|$)',
            'probleme': r'(?:\*+\s*)?PROBL[EÈ]ME\s*\*?\s*[:\-]\s*(.+?)(?=(?:\n\s*(?:\*+\s*)?(?:HOOK|SOLUTION|CTA))|$)',
            'solution': r'(?:\*+\s*)?SOLUTION\s*\*?\s*[:\-]\s*(.+?)(?=(?:\n\s*(?:\*+\s*)?(?:HOOK|PROBL[EÈ]ME|CTA))|$)',
            'cta': r'(?:\*+\s*)?CTA\s*\*?\s*[:\-]\s*(.+?)(?=(?:\n\s*(?:\*+\s*)?(?:HOOK|PROBL[EÈ]ME|SOLUTION))|$)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                content = re.sub(r'^\**\s*', '', content)
                content = re.sub(r'\s*\**\s*$', '', content)
                content = content.strip('"\'\n').strip()
                content = content.split('\n')[0].strip()
                if content:
                    result[key] = content

        return result

    def _parse_fallback(self, raw_text, fallback_hook):
        """
        Fallback intelligent : si Llama a écrit en paragraphe libre,
        on découpe par lignes/phrases et on attribue intelligemment.
        """
        result = {
            'hook': fallback_hook,
            'probleme': '',
            'solution': '',
            'cta': ''
        }

        # Nettoyer et garder les lignes non-vides
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

        # Enlever les lignes qui sont juste des labels orphelins
        lines = [l for l in lines if not re.match(r'^(HOOK|PROBL[EÈ]ME|SOLUTION|CTA)\s*[:\-]?\s*$', l, re.IGNORECASE)]

        if not lines:
            return result

        # Stratégie d'attribution :
        # - Ligne 1 (souvent) = hook ou intro
        # - Lignes du milieu = problème + solution
        # - Dernière ligne = CTA (souvent contient "lien", "code", "follow", "abonne")

        # Détecter le CTA : dernière ligne qui contient un mot clé d'action
        cta_keywords = ['lien', 'bio', 'code', 'follow', 'abonne', 'commentaire',
                        'recommande', 'suivez', 'check', 'partage']
        cta_line_idx = -1
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in cta_keywords):
                cta_line_idx = i

        if cta_line_idx >= 0:
            result['cta'] = lines[cta_line_idx]
            non_cta_lines = lines[:cta_line_idx] + lines[cta_line_idx+1:]
        else:
            # fallback : la dernière ligne devient le CTA
            result['cta'] = lines[-1]
            non_cta_lines = lines[:-1]

        # Sur les lignes restantes, séparer problème (négatif) et solution (positif)
        problem_keywords = ['avant', 'sec', 'cassant', 'terne', 'fragile', 'abîmé',
                            'problème', 'galère', 'déprimant', 'rendait']
        solution_keywords = ['depuis', 'maintenant', 'grâce', 'aide', 'transformé',
                             'changé', 'résultat', 'solution', 'efficace', 'utilise']

        problem_lines = []
        solution_lines = []

        for line in non_cta_lines:
            line_lower = line.lower()
            problem_score = sum(1 for kw in problem_keywords if kw in line_lower)
            solution_score = sum(1 for kw in solution_keywords if kw in line_lower)

            if problem_score > solution_score:
                problem_lines.append(line)
            else:
                solution_lines.append(line)

        if problem_lines:
            result['probleme'] = ' '.join(problem_lines)
        if solution_lines:
            result['solution'] = ' '.join(solution_lines)

        # Si une catégorie est vide, on rééquilibre
        if not result['probleme'] and len(non_cta_lines) >= 2:
            result['probleme'] = non_cta_lines[0] if non_cta_lines else ''
            result['solution'] = ' '.join(non_cta_lines[1:]) if len(non_cta_lines) > 1 else ''
        elif not result['solution'] and len(non_cta_lines) >= 2:
            result['solution'] = non_cta_lines[-1]

        return result


# Test direct
if __name__ == "__main__":
    from rag.retrieval import UGCRetriever
    from agents.trend_analyst import TrendAnalyst
    from agents.hook_generator import HookGenerator
    from agents.hook_critic import HookCritic

    retriever = UGCRetriever()
    analyst = TrendAnalyst(retriever)
    generator = HookGenerator()
    critic = HookCritic()
    writer = ScriptWriter()

    product = "Huile d'argan bio marocaine pour cheveux secs"

    analysis = analyst.analyze(product)
    hooks = generator.generate(product, analysis['analysis'], analysis['retrieved_ugc'])
    final = critic.select_best(hooks, product)
    script = writer.write(final['best_hook'], product, analysis['retrieved_ugc'])

    print("\n" + "="*60)
    print(f"📜 SCRIPT COMPLET pour : {product}")
    print("="*60)
    print(f"\n🎬 HOOK     : {script['structured']['hook']}")
    print(f"🤔 PROBLÈME : {script['structured']['probleme']}")
    print(f"💡 SOLUTION : {script['structured']['solution']}")
    print(f"🎯 CTA      : {script['structured']['cta']}")
    print(f"\n📊 Stats : {script['word_count']} mots, ~{script['estimated_seconds']} sec")
    print("="*60)