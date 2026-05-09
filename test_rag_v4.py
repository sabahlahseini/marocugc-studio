"""
MarocUGC Studio - Test #4 : RAG amélioré (V4)
Améliorations : filtrage métadonnées + contexte réduit + instructions précises
"""

import ollama
import chromadb
from sentence_transformers import SentenceTransformer

# ============================================
# 1. SETUP
# ============================================
print("🔧 Chargement du système RAG V4...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="ugc_collection")
print(f"✅ {collection.count()} UGC indexés disponibles\n")


# ============================================
# 2. FONCTION : détecter la catégorie du produit
# ============================================
def detect_product_category(product_description):
    """
    Détecte si le produit est skincare, haircare, ou autre.
    Approche simple par mots-clés (on pourrait utiliser un classifieur en V5).
    """
    product_lower = product_description.lower()
    
    haircare_keywords = ['cheveu', 'capillaire', 'shampoo', 'shampooing', 
                         'hair', 'masque cheveux', 'apres-shampoing']
    skincare_keywords = ['peau', 'crème', 'creme', 'sérum', 'serum', 
                         'visage', 'anti-age', 'anti-âge', 'skincare', 
                         'hydrat', 'éclat', 'eclat', 'argan', 'safran']
    
    if any(kw in product_lower for kw in haircare_keywords):
        return 'haircare'
    elif any(kw in product_lower for kw in skincare_keywords):
        return 'skincare'
    else:
        return None  # pas de filtre


# ============================================
# 3. FONCTION : RAG avec filtrage
# ============================================
def retrieve_relevant_ugc_filtered(product_query, n_results=3):
    """Cherche les UGC pertinents en filtrant par sous-catégorie."""
    
    # Détecter la catégorie
    category = detect_product_category(product_query)
    print(f"   🏷️  Catégorie détectée : {category if category else 'aucune (pas de filtre)'}")
    
    # Vectoriser la requête
    query_embedding = embedding_model.encode(product_query).tolist()
    
    # Construire le filtre ChromaDB
    where_filter = {}
    if category:
        where_filter = {"subcategory": category}
    
    # Recherche avec filtre
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter if where_filter else None
    )
    
    return results


# ============================================
# 4. PROMPT V4 : précis, contexte réduit
# ============================================
def build_rag_prompt_v4(product_description, retrieved_ugc):
    """V4 : on injecte SEULEMENT les hooks (pas les scripts), avec instruction claire."""
    
    # Extraire uniquement les hooks (pas les scripts complets)
    hooks_examples = ""
    for i in range(len(retrieved_ugc['ids'][0])):
        hook = retrieved_ugc['documents'][0][i]
        format_type = retrieved_ugc['metadatas'][0][i]['format_type']
        hooks_examples += f"- Pattern '{format_type}' : {hook}\n"
    
    system = """Tu es un expert UGC viral pour TikTok.

RÈGLES STRICTES:
- Hook MAXIMUM 12 mots
- Imite le STYLE et le PATTERN des exemples (POV, Wait, Personne ne sait...)
- N'IMITE PAS le contenu : si l'exemple parle de cheveux et le produit est une crème, parle de la crème
- Adapte au produit demandé
- Ton naturel, jamais publicitaire
- Pas de hashtags, pas d'emojis
- INTERDICTION d'inventer des mots"""
    
    user = f"""Voici 3 patterns viraux qui marchent bien :

{hooks_examples}

Maintenant génère UN SEUL hook viral pour ce produit en t'inspirant des PATTERNS ci-dessus :

PRODUIT : {product_description}

⚠️ Le hook doit parler du PRODUIT, pas répéter le contenu des exemples.

Donne uniquement le hook, rien d'autre."""
    
    return system, user


# ============================================
# 5. FONCTION : générer un hook avec RAG V4
# ============================================
def generate_hook_v4(product_description):
    print(f"\n🔍 RAG V4 : recherche pour '{product_description}'...")
    
    retrieved = retrieve_relevant_ugc_filtered(product_description, n_results=3)
    
    print("   📚 UGC trouvés (filtrés) :")
    for i in range(len(retrieved['ids'][0])):
        ugc_id = retrieved['ids'][0][i]
        hook = retrieved['documents'][0][i]
        sim = (1 - retrieved['distances'][0][i]) * 100
        subcat = retrieved['metadatas'][0][i]['subcategory']
        print(f"      • [{ugc_id}] {sim:.1f}% [{subcat}] → {hook}")
    
    print("\n   🤖 Llama génère...")
    system, user = build_rag_prompt_v4(product_description, retrieved)
    
    response = ollama.chat(
        model='llama3.2:3b',
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ]
    )
    
    return response['message']['content']


# ============================================
# 6. TEST sur les mêmes produits que V3
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
    
    hook = generate_hook_v4(product)
    
    print(f"\n🎬 HOOK GÉNÉRÉ (RAG v4) :")
    print(f"   → {hook}")
    print()