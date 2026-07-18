"""
Routes de l'API — définit les endpoints exposés au frontend.
"""

from fastapi import APIRouter, HTTPException

from src.agents.customer_service_agent import answer_question
from src.rag.retrieval import search
from src.api.schemas import ChatRequest, ChatResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Reçoit une question, retourne la réponse de l'agent service client + ses sources."""

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    try:
        answer_text = answer_question(request.question)

        chunks = search(request.question)
        sources = list({c.metadata.get("product_name", "?") for c in chunks})
        # ↑ set (accolades {}) pour dédupliquer automatiquement les noms
        #   de produits si plusieurs chunks viennent du même produit,
        #   puis converti en liste pour que Pydantic puisse le sérialiser

        return ChatResponse(answer=answer_text, sources=sources)

    except Exception as exc:
        logger.error("Erreur lors du traitement de la question : %s", exc)
        raise HTTPException(status_code=500, detail="Erreur interne lors du traitement.")


@router.get("/health")
def health() -> dict:
    """Endpoint de vérification — confirme que l'API est vivante."""
    return {"status": "ok"}