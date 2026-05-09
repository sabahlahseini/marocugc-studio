"""
MarocUGC Studio - Module RAG centralisé
Toutes les fonctions de recherche sémantique passent par ici.
"""

import chromadb
from sentence_transformers import SentenceTransformer


class UGCRetriever:
    """Classe pour faire du RAG sur la collection d'UGC viraux."""
    
    def __init__(self, db_path="./chroma_db", collection_name="ugc_collection"):
        print("🔧 Initialisation du retriever RAG...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(name=collection_name)
        print(f"✅ {self.collection.count()} UGC indexés disponibles")
    
    
    def detect_category(self, product_description):
        """Détecte la sous-catégorie du produit (skincare/haircare/None)."""
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
        return None
    
    
    def search(self, query, n_results=3, filter_category=True):
        """
        Cherche les n_results UGC les plus similaires à la query.
        
        Args:
            query: texte de la requête
            n_results: nombre de résultats à retourner
            filter_category: si True, filtre par sous-catégorie détectée
        
        Returns:
            liste de dicts {id, hook, format_type, similarity, full_script, ...}
        """
        # Détection de catégorie
        category = self.detect_category(query) if filter_category else None
        
        # Vectorisation
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Construction du filtre
        where_filter = {"subcategory": category} if category else None
        
        # Recherche
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )
        
        # Formatage propre des résultats
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'hook': results['documents'][0][i],
                'similarity': round((1 - results['distances'][0][i]) * 100, 2),
                'format_type': results['metadatas'][0][i]['format_type'],
                'full_script': results['metadatas'][0][i]['full_script'],
                'engagement': results['metadatas'][0][i]['engagement'],
                'subcategory': results['metadatas'][0][i]['subcategory']
            })
        
        return {
            'detected_category': category,
            'results': formatted
        }


# Test rapide si on lance ce fichier directement
if __name__ == "__main__":
    retriever = UGCRetriever()
    
    print("\n--- Test rapide ---")
    output = retriever.search("Huile d'argan pour cheveux secs", n_results=3)
    print(f"\nCatégorie détectée : {output['detected_category']}")
    for r in output['results']:
        print(f"  • [{r['id']}] ({r['similarity']}%) [{r['format_type']}] → {r['hook']}")