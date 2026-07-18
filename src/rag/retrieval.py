"""
Recherche dans l'index vectoriel (retrieval).

Réutilise l'index déjà construit par indexing.py — ce fichier ne
construit rien, il propose juste une fonction de recherche propre,
avec les réglages définis dans config.py (RETRIEVAL_TOP_K, USE_MMR).
"""

from langchain_core.documents import Document

from src.rag.indexing import get_vector_store  
from src.utils.logger import get_logger
from config import RETRIEVAL_TOP_K, USE_MMR

logger = get_logger(__name__)


def search(query: str, k: int = RETRIEVAL_TOP_K) -> list[Document]:
    """Cherche les k chunks les plus pertinents pour une question donnée."""

    vector_store = get_vector_store()
    # ↑ se connecte à l'index déjà existant sur disque (chroma_db/),
    #   ne recalcule AUCUN embedding — juste une connexion en lecture

    if USE_MMR:
        results = vector_store.max_marginal_relevance_search(query, k=k)
        # ↑ pertinence + diversité (voir explication au-dessus)
    else:
        results = vector_store.similarity_search(query, k=k)
        # ↑ pertinence pure, peut renvoyer des résultats redondants

    logger.info("Recherche '%s' — %d résultats (MMR=%s)", query, len(results), USE_MMR)
    return results


def format_results_for_display(results: list[Document]) -> str:
    """Formate les résultats pour un affichage lisible en console."""
    lines = []
    for i, doc in enumerate(results, start=1):
        name = doc.metadata.get("product_name", "?")
        brand = doc.metadata.get("brand", "?")
        lines.append(f"{i}. {name} ({brand})")
    return "\n".join(lines)


if __name__ == "__main__":
    test_queries = [
        "yaourt sans lactose",
        "boisson gazeuse au cola",
        "produit avec des cacahuètes",
    ]

    for query in test_queries:
        results = search(query)
        print(f"\n--- Question : '{query}' ---")
        print(format_results_for_display(results))