"""
MarocUGC Studio - Agent 1 : Trend Analyst
Mission : analyser le produit, identifier les patterns viraux pertinents.
"""

import ollama
from rag.retrieval import UGCRetriever


class TrendAnalyst:
    """Agent qui analyse le produit et propose les patterns viraux à utiliser."""
    
    def __init__(self, retriever: UGCRetriever, llm_model='llama3.2:3b'):
        self.retriever = retriever
        self.llm_model = llm_model
        self.system_prompt = """Tu es un expert en analyse de tendances UGC pour TikTok.
Ta mission : analyser un produit et recommander 3 patterns viraux pertinents.

RÈGLES :
- Sois concis et stratégique
- Justifie chaque pattern en 1 phrase
- Format de sortie STRICT (JSON)
- Pas de blabla, juste l'analyse"""
    
    
    def analyze(self, product_description):
        """
        Analyse un produit et retourne :
        - Les UGC pertinents trouvés via RAG
        - Les 3 patterns recommandés avec justification
        """
        print(f"\n🔍 [Agent 1: Trend Analyst] Analyse de '{product_description}'...")
        
        # 1. RAG : récupérer des UGC similaires
        rag_output = self.retriever.search(product_description, n_results=5)
        retrieved_ugc = rag_output['results']
        category = rag_output['detected_category']
        
        print(f"   🏷️  Catégorie : {category}")
        print(f"   📚 {len(retrieved_ugc)} UGC viraux trouvés pour inspiration")
        
        # 2. Préparer la liste des patterns observés
        patterns_observed = list(set([ugc['format_type'] for ugc in retrieved_ugc]))
        patterns_text = "\n".join([
            f"- {ugc['format_type']} (engagement {ugc['engagement']:,}) : {ugc['hook']}"
            for ugc in retrieved_ugc
        ])
        
        # 3. Demander au LLM de recommander 3 patterns
        user_prompt = f"""PRODUIT : {product_description}

PATTERNS VIRAUX OBSERVÉS dans des UGC similaires :
{patterns_text}

Analyse ce produit et recommande LES 3 MEILLEURS patterns à utiliser pour un hook viral.

Réponds STRICTEMENT en JSON, sans backticks, sans explication avant/après :
{{
  "category": "{category}",
  "recommended_patterns": [
    {{"pattern": "POV", "reason": "Une phrase justifiant"}},
    {{"pattern": "Wait", "reason": "Une phrase justifiant"}},
    {{"pattern": "Numbered_Story", "reason": "Une phrase justifiant"}}
  ],
  "key_angles": ["angle1", "angle2", "angle3"]
}}"""
        
        print("   🤖 LLM réfléchit...")
        response = ollama.chat(
            model=self.llm_model,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        )
        
        analysis_text = response['message']['content']
        
        # 4. Tenter de parser le JSON (avec gestion d'erreur si Llama foire)
        import json
        import re
        
        # Extraire le JSON même si Llama met du texte autour
        json_match = re.search(r'\{[\s\S]*\}', analysis_text)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
            except json.JSONDecodeError:
                analysis = {"error": "JSON parsing failed", "raw": analysis_text}
        else:
            analysis = {"error": "No JSON found", "raw": analysis_text}
        
        # 5. Retour structuré
        return {
            'product': product_description,
            'category': category,
            'retrieved_ugc': retrieved_ugc,
            'analysis': analysis
        }


# Test si on lance ce fichier directement
if __name__ == "__main__":
    retriever = UGCRetriever()
    analyst = TrendAnalyst(retriever)
    
    test_products = [
        "Huile d'argan bio marocaine pour cheveux secs",
        "Crème anti-âge à la figue de barbarie"
    ]
    
    for product in test_products:
        result = analyst.analyze(product)
        print(f"\n{'='*60}")
        print(f"📦 PRODUIT : {result['product']}")
        print(f"🏷️  CATÉGORIE : {result['category']}")
        print(f"\n📊 ANALYSE :")
        import json
        print(json.dumps(result['analysis'], indent=2, ensure_ascii=False))
        print(f"{'='*60}\n")