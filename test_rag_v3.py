"""
MarocUGC Studio - Test #3 : RAG complet (le vrai)
On combine Llama + ChromaDB pour des hooks inspirés de UGC viraux réels
"""

import ollama
import chromadb
from sentence_transformers import SentenceTransformer

# ============================================
# 1. SETUP : charger le modèle d'embeddings + DB
# ============================================
print("🔧 Chargement du système RAG...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="ugc_collection")
print(f"✅ {collection.count()} UGC indexés disponibles\n")


# ============================================
# 2. FONCTION : récupérer les UGC pertinents
# ============================================
def retrieve_relevant_ugc(product_query, n_results=3):
    """Cherche les n_results UGC les plus similaires au produit demandé."""
    query_embedding = embedding_model.encode(product_query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results


# ============================================
# 3. FONCTION : construire le prompt avec RAG
# ============================================
def build_rag_prompt(product_description, retrieved_ugc):
    """Construit un prompt structuré qui injecte les UGC retrouvés."""
    
    # Formater les UGC retrouvés en exemples
    examples_text = "Voici 3 hooks viraux pertinents pour t'inspirer :\n\n"
    for i in range(len(retrieved_ugc['ids'][0])):
        hook = retrieved_ugc['documents'][0][i]
        format_type = retrieved_ugc['metadatas'][0][i]['format_type']
        full_script = retrieved_ugc['metadatas'][0][i]['full_script']
        engagement = retrieved_ugc['metadatas'][0][i]['engagement']
        
        examples_text += f"EXEMPLE {i+1} (format: {format_type}, {engagement:,} engagements) :\n"
        examples_text += f"Hook: {hook}\n"
        examples_text += f"Script complet: {full_script}\n\n"
    
    # System prompt
    system = """Tu es un expert UGC viral pour TikTok et Instagram, 
spécialisé dans le marché marocain (français/darija).

RÈGLES STRICTES:
- Hook MAXIMUM 12 mots (3 secondes oral)
- Inspire-toi des patterns des exemples (POV, Wait, J'ai testé...)
- Ton naturel, JAMAIS publicitaire
- Pas de hashtags dans le hook
- Pas d'emojis dans le hook
- Adapte le pattern au produit demandé
- INTERDICTION d'inventer des mots ou expressions"""
    
    # User prompt
    user = f"""{examples_text}

Maintenant génère UN SEUL hook viral pour ce produit :

PRODUIT: {product_description}
PLATEFORME: TikTok

Donne juste le hook, rien d'autre."""
    
    return system, user


# ============================================
# 4. FONCTION : générer un hook avec RAG
# ============================================
def generate_hook_with_rag(product_description):
    print(f"\n🔍 RAG: recherche d'UGC similaires pour '{product_description}'...")
    retrieved = retrieve_relevant_ugc(product_description, n_results=3)
    
    print("📚 UGC trouvés:")
    for i in range(len(retrieved['ids'][0])):
        ugc_id = retrieved['ids'][0][i]
        hook = retrieved['documents'][0][i]
        sim = (1 - retrieved['distances'][0][i]) * 100
        print(f"   • [{ugc_id}] {sim:.1f}% → {hook}")
    
    print("\n🤖 Llama génère un hook inspiré...")
    system, user = build_rag_prompt(product_description, retrieved)
    
    response = ollama.chat(
        model='llama3.2:3b',
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ]
    )
    
    return response['message']['content']


# ============================================
# 5. TEST : générer pour 3 produits différents
# ============================================
test_products = [
    "Huile d'argan bio marocaine pure pour cheveux secs",
    "Crème anti-âge naturelle aux extraits de figue de barbarie",
    "Sérum éclat à base de safran marocain"
]

for product in test_products:
    print("\n" + "="*60)
    print(f"📦 PRODUIT : {product}")
    print("="*60)
    
    hook = generate_hook_with_rag(product)
    
    print(f"\n🎬 HOOK GÉNÉRÉ (RAG v3) :")
    print(f"   → {hook}")
    print()