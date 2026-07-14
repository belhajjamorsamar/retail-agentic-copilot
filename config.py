"""
Configuration centralisée du projet..
"""
# --- Phase 1 : extraction du catalogue Open Food Facts ---
OPEN_FOOD_FACTS_API_URL = "https://world.openfoodfacts.org/api/v2/search"
# --- Phase 2 : RAG (agent service client) ---
LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

RETRIEVAL_TOP_K = 4
USE_MMR = True

CHROMA_PERSIST_DIR = "chroma_db"
CHROMA_COLLECTION_NAME = "retail_catalog"