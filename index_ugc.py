"""
MarocUGC Studio - Indexation du dataset UGC dans ChromaDB
Étape : transformer les UGC en vecteurs et les stocker pour le RAG
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer

# 1. CHARGER LES UGC depuis le JSON
print("📂 Chargement du dataset...")
with open('data/ugc_dataset.json', 'r', encoding='utf-8') as f:
    ugc_list = json.load(f)
print(f"✅ {len(ugc_list)} UGC chargés")

# 2. CHARGER LE MODÈLE D'EMBEDDINGS
# all-MiniLM-L6-v2 : rapide, multilingue (basique), 384 dimensions
print("\n🧠 Chargement du modèle d'embeddings...")
print("   (Premier run = téléchargement de ~80 Mo, soyez patient)")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Modèle chargé")

# 3. CRÉER UNE COLLECTION CHROMADB
print("\n💾 Initialisation de ChromaDB...")
client = chromadb.PersistentClient(path="./chroma_db")

# Si la collection existe déjà, on la supprime pour repartir propre
try:
    client.delete_collection(name="ugc_collection")
    print("   (Ancienne collection supprimée)")
except:
    pass

collection = client.create_collection(
    name="ugc_collection",
    metadata={"hnsw:space": "cosine"}  # Force la cosine similarity
)
print("✅ Collection créée")

# 4. VECTORISER ET INDEXER CHAQUE UGC
print("\n🔢 Vectorisation et indexation des UGC...")

# On va indexer le HOOK comme texte principal (ce sur quoi on cherche)
# Les autres infos (full_script, category, etc.) sont stockées en métadonnées

hooks = [ugc['hook'] for ugc in ugc_list]
ids = [ugc['id'] for ugc in ugc_list]

# Calcul des embeddings (transforme chaque hook en vecteur de 384 nombres)
embeddings = model.encode(hooks).tolist()

# Préparation des métadonnées (tout sauf le hook)
metadatas = []
for ugc in ugc_list:
    metadatas.append({
        'category': ugc['category'],
        'subcategory': ugc['subcategory'],
        'language': ugc['language'],
        'format_type': ugc['format_type'],
        'engagement': ugc['engagement'],
        'platform': ugc['platform'],
        'full_script': ugc['full_script']  # important pour le RAG ensuite
    })

# Ajout en masse dans ChromaDB
collection.add(
    embeddings=embeddings,
    documents=hooks,
    metadatas=metadatas,
    ids=ids
)

print(f"✅ {len(ugc_list)} UGC indexés avec succès")

# 5. VÉRIFICATION : combien d'éléments dans la collection ?
print(f"\n📊 Total dans la collection : {collection.count()} UGC")
print("\n🎉 Indexation terminée. La DB est dans ./chroma_db/")