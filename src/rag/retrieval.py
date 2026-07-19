"""
Recherche dans l'index vectoriel (retrieval).

Combine recherche sémantique (embeddings + MMR) et recherche par mot-clé
exact dans le catalogue. La recherche sémantique seule peut rater des
termes précis (allergènes, ingrédients spécifiques) — observé concrètement
sur des questions comme "produits avec des cacahuètes". La recherche par
mot-clé compense cette limite en cherchant une correspondance textuelle
directe, en complément.
"""

import json

from langchain_core.documents import Document

from src.rag.indexing import get_vector_store
from src.utils.logger import get_logger
from config import RETRIEVAL_TOP_K, USE_MMR

logger = get_logger(__name__)

CATALOG_PATH = "data/raw/catalog_clean.json"


def keyword_search(query: str, max_results: int = 3) -> list[dict]:
    """Recherche par mot-clé exact dans le catalogue."""
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    stopwords = {"les", "des", "qui", "que", "a", "de", "le", "la", "un", "une", "et", "donner", "avec"}
    keywords = [w.lower() for w in query.split() if len(w) > 3 and w.lower() not in stopwords]

    matches = []
    for product in catalog:
        searchable_text = (
            product.get("ingredients_text", "") + " " +
            product.get("product_name", "") + " " +
            product.get("allergens", "")
        ).lower()

        if any(kw in searchable_text for kw in keywords):
            matches.append(product)

    return matches[:max_results]


def search(query: str, k: int = RETRIEVAL_TOP_K) -> list[Document]:
    """Combine recherche sémantique et recherche par mot-clé."""

    vector_store = get_vector_store()

    if USE_MMR:
        semantic_results = vector_store.max_marginal_relevance_search(query, k=k)
    else:
        semantic_results = vector_store.similarity_search(query, k=k)

    keyword_matches = keyword_search(query)
    keyword_docs = [
        Document(
            page_content=(
                f"Produit : {p['product_name']}\nMarque : {p['brand']}\n"
                f"Ingrédients : {p['ingredients_text']}\nAllergènes : {p['allergens']}"
            ),
            metadata={"code": p["code"], "product_name": p["product_name"], "brand": p["brand"]},
        )
        for p in keyword_matches
    ]

    seen_codes = {d.metadata.get("code") for d in semantic_results}
    combined = semantic_results + [d for d in keyword_docs if d.metadata.get("code") not in seen_codes]

    logger.info(
        "Recherche '%s' — %d résultats sémantiques + %d résultats mot-clé ajoutés",
        query, len(semantic_results), len(combined) - len(semantic_results),
    )
    return combined


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