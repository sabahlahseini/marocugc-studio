"""
MarocUGC Studio - Test de la recherche sémantique
On interroge ChromaDB avec différentes queries pour voir si elle trouve les bons UGC
"""

import chromadb
from sentence_transformers import SentenceTransformer

# 1. Recharger le modèle et la DB
print("🔧 Chargement du système RAG...")
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="ugc_collection")
print(f"✅ {collection.count()} UGC indexés disponibles\n")


def search_similar_ugc(query, n_results=3):
    """Cherche les n_results UGC les plus similaires à la query."""
    # Vectoriser la requête
    query_embedding = model.encode(query).tolist()
    
    # Chercher dans ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results


# 2. Tester avec plusieurs requêtes
test_queries = [
    "huile d'argan pour cheveux secs",
    "produit anti-âge naturel",
    "routine beauté simple et économique",
    "skincare for dry skin"
]

for query in test_queries:
    print("="*60)
    print(f"🔎 QUERY : {query}")
    print("="*60)
    
    results = search_similar_ugc(query, n_results=3)
    
    # Afficher les 3 UGC les plus proches
    for i in range(len(results['ids'][0])):
        ugc_id = results['ids'][0][i]
        hook = results['documents'][0][i]
        format_type = results['metadatas'][0][i]['format_type']
        distance = results['distances'][0][i]
        
        # Plus la distance est petite, plus c'est similaire
        similarity = 1 - distance
        
        print(f"\n  #{i+1} [{ugc_id}] (similarité: {similarity:.2%})")
        print(f"      Format : {format_type}")
        print(f"      Hook   : {hook}")
    
    print()