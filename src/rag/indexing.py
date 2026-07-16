"""
Indexation des chunks : embeddings + stockage dans ChromaDB.

Décision importante : avant de tout ré-indexer, on vérifie si un index
existe déjà. Régénérer des embeddings à chaque test coûterait de l'argent
inutilement (appel API OpenAI facturé à chaque embedding) — un vrai
risque identifié tôt dans ce projet. On ne ré-indexe que si demandé
explicitement (force=True) ou si aucun index n'existe encore.
"""

from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.rag.build_documents import build_documents
from src.rag.chunking import chunk_documents
from src.utils.logger import get_logger
from config import EMBEDDING_MODEL, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

logger = get_logger(__name__)


def get_vector_store() -> Chroma:
    """Retourne l'objet Chroma connecté à notre collection persistante."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
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

    logger.info("Construction d'un nouvel index (appels API OpenAI en cours)...")

    docs = build_documents()
    chunks = chunk_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    # ↑ from_documents() fait TOUT en une ligne : transforme chaque chunk
    #   en embedding (appel API OpenAI), puis les stocke dans ChromaDB,
    #   puis sauvegarde sur disque (persist_directory)

    logger.info("Index construit et sauvegardé : %d chunks indexés", len(chunks))
    return vector_store


if __name__ == "__main__":
    vector_store = build_index()

    # Test rapide : une recherche de similarité pour vérifier que l'index marche
    results = vector_store.similarity_search("yaourt sans lactose", k=3)
    logger.info("Test de recherche — 'yaourt sans lactose' :")
    for i, doc in enumerate(results):
        logger.info("Résultat %d : %s", i + 1, doc.metadata.get("product_name"))