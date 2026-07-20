"""
Indexation des chunks : embeddings + stockage dans ChromaDB.

Décision importante : avant de tout ré-indexer, on vérifie si un index
existe déjà. Régénérer des embeddings à chaque test coûterait du temps et
de l'argent inutilement — un vrai risque identifié tôt dans ce projet. On
ne ré-indexe que si demandé explicitement (force=True) ou si aucun index
n'existe encore.

Le modèle d'embedding est mis en cache (get_embeddings) pour n'être chargé
qu'une seule fois en mémoire, plutôt qu'à chaque appel de get_vector_store()
— ça évite plusieurs secondes de rechargement à chaque question posée.
"""

from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src.rag.build_documents import build_documents
from src.rag.chunking import chunk_documents
from src.utils.logger import get_logger
from config import EMBEDDING_MODEL, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

logger = get_logger(__name__)

# Cache du modèle d'embedding — évite de le recharger à chaque appel
_embeddings_cache = None


def get_embeddings():
    """Retourne le modèle d'embedding, chargé une seule fois (mis en cache)."""
    global _embeddings_cache
    if _embeddings_cache is None:
        _embeddings_cache = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings_cache


def get_vector_store() -> Chroma:
    """Retourne l'objet Chroma connecté à notre collection persistante."""
    embeddings = get_embeddings()
    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )


def index_already_exists() -> bool:
    """Vérifie si un index ChromaDB existe déjà sur le disque."""
    path = Path(CHROMA_PERSIST_DIR)
    return path.exists() and any(path.iterdir())


def build_index(force: bool = False) -> Chroma:
    """Construit (ou recharge) l'index vectoriel à partir du catalogue."""

    if index_already_exists() and not force:
        logger.info(
            "Index déjà existant dans '%s' — chargement sans ré-indexer "
            "(passe force=True pour forcer la ré-indexation)",
            CHROMA_PERSIST_DIR,
        )
        return get_vector_store()

    logger.info("Construction d'un nouvel index...")

    docs = build_documents()
    chunks = chunk_documents(docs)
    embeddings = get_embeddings()  # ← utilise le cache aussi ici, pas de nouvel objet

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
    )

    logger.info("Index construit et sauvegardé : %d chunks indexés", len(chunks))
    return vector_store


if __name__ == "__main__":
    vector_store = build_index()
    results = vector_store.similarity_search("yaourt sans lactose", k=3)
    logger.info("Test de recherche — 'yaourt sans lactose' :")
    for i, doc in enumerate(results):
        logger.info("Résultat %d : %s", i + 1, doc.metadata.get("product_name"))