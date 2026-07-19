"""
Chunking des documents produit.

Approche : on applique RecursiveCharacterTextSplitter à TOUS les documents
de façon uniforme. Pour la majorité des produits (texte court), le
splitter renvoie un seul chunk identique au document d'origine — le
découpage ne se déclenche réellement que pour les produits avec un texte
long (ex : listes d'ingrédients très détaillées), qu'on a observées dans
notre catalogue. C'est un filet de sécurité, pas un découpage forcé.
"""

from collections import Counter

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.rag.build_documents import build_documents
from src.utils.logger import get_logger
from config import CHUNK_SIZE, CHUNK_OVERLAP

logger = get_logger(__name__)


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Découpe les documents trop longs, laisse les courts intacts."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    codes = Counter(c.metadata["code"] for c in chunks)
    multi_chunk_products = sum(1 for count in codes.values() if count > 1)

    logger.info(
        "Chunking terminé : %d chunks au total, %d produits découpés en plusieurs chunks",
        len(chunks), multi_chunk_products,
    )
    return chunks


if __name__ == "__main__":
    docs = build_documents()
    chunks = chunk_documents(docs)

    codes = Counter(c.metadata["code"] for c in chunks)
    multi = [code for code, count in codes.items() if count > 1]

    if multi:
        example_chunks = [c for c in chunks if c.metadata["code"] == multi[0]]
        logger.info("Exemple de produit découpé (%s) en %d chunks :", multi[0], len(example_chunks))
        for i, c in enumerate(example_chunks):
            logger.info("--- Chunk %d ---\n%s", i + 1, c.page_content)
    else:
        logger.info("Aucun produit n'a nécessité d'être découpé en plusieurs chunks.")