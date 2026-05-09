"""
MarocUGC Studio - Pipeline Orchestrator
Le point d'entrée principal qui coordonne les 5 agents.
"""

from rag.retrieval import UGCRetriever
from agents.trend_analyst import TrendAnalyst
from agents.hook_generator import HookGenerator
from agents.hook_critic import HookCritic
from agents.script_writer import ScriptWriter
from agents.hashtag_optimizer import HashtagOptimizer

import time
import json


class MarocUGCStudio:
    """
    Orchestrateur principal de MarocUGC Studio.
    Coordonne les 5 agents pour générer un brief UGC complet.
    """

    def __init__(self):
        print("\n" + "="*60)
        print("🎬 MarocUGC Studio — Initialisation")
        print("="*60)

        # Charger tous les agents
        self.retriever = UGCRetriever()
        self.analyst = TrendAnalyst(self.retriever)
        self.generator = HookGenerator()
        self.critic = HookCritic()
        self.writer = ScriptWriter()
        self.hashtag_optimizer = HashtagOptimizer()

        print("\n✅ Tous les agents sont prêts\n")

    def generate(self, product, platform="TikTok", verbose=True):
        """
        Génère un brief UGC complet pour un produit.

        Args:
            product: description du produit
            platform: TikTok / Instagram (info, pas encore utilisée par les agents)
            verbose: afficher les étapes intermédiaires

        Returns:
            dict avec tout le brief structuré
        """
        start_time = time.time()

        if verbose:
            print("\n" + "="*60)
            print(f"🎯 GÉNÉRATION pour : {product}")
            print(f"📱 Plateforme : {platform}")
            print("="*60)

        # ÉTAPE 1 : Trend Analyst
        analysis_result = self.analyst.analyze(product)

        # ÉTAPE 2 : Hook Generator
        hooks = self.generator.generate(
            product=product,
            analysis=analysis_result['analysis'],
            retrieved_ugc=analysis_result['retrieved_ugc']
        )

        # ÉTAPE 3 : Hook Critic
        best = self.critic.select_best(hooks, product)

        # ÉTAPE 4 : Script Writer
        script = self.writer.write(
            hook=best['best_hook'],
            product=product,
            retrieved_ugc=analysis_result['retrieved_ugc']
        )

        # ÉTAPE 5 : Hashtag Optimizer
        hashtags = self.hashtag_optimizer.generate(
            product=product,
            hook=best['best_hook'],
            category=analysis_result['category']
        )

        elapsed = time.time() - start_time

        # Construire le brief final
        brief = {
            'product': product,
            'platform': platform,
            'category': analysis_result['category'],
            'generation_time_seconds': round(elapsed, 1),
            'inspired_by': [
                {
                    'hook': ugc['hook'],
                    'similarity': ugc['similarity'],
                    'engagement': ugc['engagement']
                }
                for ugc in analysis_result['retrieved_ugc'][:3]
            ],
            'all_hook_candidates': hooks,
            'best_hook': best['best_hook'],
            'hook_score': best['score'],
            'script': script['structured'],
            'script_full_text': script['full_text'],
            'estimated_video_seconds': script['estimated_seconds'],
            'hashtags': {
                'broad': hashtags['broad'],
                'niche': hashtags['niche'],
                'trending': hashtags['trending'],
                'all': hashtags['all']
            }
        }

        if verbose:
            self._print_brief(brief)

        return brief

    def _print_brief(self, brief):
        """Affiche le brief de façon lisible."""
        print("\n" + "="*60)
        print("🎬 BRIEF UGC FINAL")
        print("="*60)
        print(f"\n📦 Produit  : {brief['product']}")
        print(f"📱 Plateforme : {brief['platform']}")
        print(f"🏷️  Catégorie : {brief['category']}")
        print(f"⏱️  Temps de génération : {brief['generation_time_seconds']}s")

        print("\n" + "-"*60)
        print("🎬 SCRIPT")
        print("-"*60)
        print(f"HOOK     : {brief['script']['hook']}")
        print(f"PROBLÈME : {brief['script']['probleme']}")
        print(f"SOLUTION : {brief['script']['solution']}")
        print(f"CTA      : {brief['script']['cta']}")
        print(f"\n📊 {brief['estimated_video_seconds']} secondes estimées")

        print("\n" + "-"*60)
        print("🏷️  HASHTAGS")
        print("-"*60)
        print(f"BROAD     : {' '.join(brief['hashtags']['broad'])}")
        print(f"NICHE     : {' '.join(brief['hashtags']['niche'])}")
        print(f"TRENDING  : {' '.join(brief['hashtags']['trending'])}")

        print("\n" + "-"*60)
        print("💡 INSPIRÉ DE")
        print("-"*60)
        for ugc in brief['inspired_by']:
            print(f"  • {ugc['similarity']}% — {ugc['hook'][:60]}...")

        print("\n" + "="*60)


# ============================================
# Point d'entrée principal
# ============================================
if __name__ == "__main__":
    # Initialiser le studio
    studio = MarocUGCStudio()

    # Test avec UN produit
    product = "Huile d'argan bio marocaine pour cheveux secs"

    brief = studio.generate(product, platform="TikTok")

    # Sauvegarder le brief en JSON
    with open('last_brief.json', 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    print("\n💾 Brief sauvegardé dans last_brief.json")