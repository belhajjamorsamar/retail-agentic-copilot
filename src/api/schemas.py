"""
Schémas Pydantic pour l'API — définissent la forme exacte des requêtes
et réponses, validées automatiquement par FastAPI.
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Ce que le frontend envoie."""
    question: str


class ChatResponse(BaseModel):
    """Ce que l'API renvoie."""
    answer: str
    sources: list[str]
    # ↑ noms des produits cités, pour que le frontend puisse les afficher
    #   séparément de la réponse texte si besoin (ex: en tags cliquables)