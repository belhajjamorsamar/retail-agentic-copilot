"""
Transformation du catalogue propre en documents texte pour le RAG.

Décision : pas de chunking agressif ici. Un produit tient en quelques
phrases — le fragmenter romprait le lien entre son nom, ses ingrédients
et ses allergènes. Contrairement à un long document (cours, rapport), un
produit de catalogue est déjà une unité de sens compacte : un produit =
un document.
"""

import json
from pathlib import Path

from langchain_core.documents import Document

from src.utils.logger import get_logger

logger = get_logger(__name__)

CATALOG_PATH = "data/raw/catalog_clean.json"


def product_to_text(product: dict) -> str:
    """Convertit un produit en texte lisible, celui qui sera indexé."""
    return (
        f"Produit : {product['product_name']}\n"
        f"Marque : {product['brand']}\n"
        f"Catégorie : {product['category']}\n"
        f"Quantité : {product['quantity']}\n"
        f"Ingrédients : {product['ingredients_text']}\n"
        f"Allergènes : {product['allergens']}"
    )


def build_documents(catalog_path: str = CATALOG_PATH) -> list[Document]:
    """Charge le catalogue propre et le convertit en documents LangChain."""
    with open(catalog_path, encoding="utf-8") as f:
        catalog = json.load(f)

    documents = []
    for product in catalog:
        text = product_to_text(product)
        # ↑ le texte lisible qui sera transformé en embedding

        metadata = {
            "code": product["code"],
            "product_name": product["product_name"],
            "brand": product["brand"],
            "category": product["category"],
        }
        # ↑ les métadonnées ne sont PAS indexées sémantiquement, mais
        #   voyagent avec le document — c'est ce qui permettra de citer
        #   la source exacte dans la réponse finale de l'agent

        documents.append(Document(page_content=text, metadata=metadata))

    logger.info("Documents construits : %d (à partir de %d produits)", len(documents), len(catalog))
    return documents


if __name__ == "__main__":
    docs = build_documents()
    logger.info("Exemple de document :\n%s", docs[0].page_content)
    logger.info("Métadonnées de l'exemple : %s", docs[0].metadata)