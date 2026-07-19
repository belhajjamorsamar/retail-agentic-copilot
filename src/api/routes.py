"""
Routes de l'API — définit les endpoints exposés au frontend.
"""

from fastapi import APIRouter, HTTPException

from src.orchestration.supervisor import run_supervisor
from src.rag.retrieval import search
from src.api.schemas import ChatRequest, ChatResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Reçoit une question, retourne la réponse du superviseur (RAG et/ou stock) + ses sources."""

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    try:
        answer_text = run_supervisor(request.question)
        # ↑ changement clé : on passe par le superviseur, plus par le RAG seul

        chunks = search(request.question)
        sources = list({c.metadata.get("product_name", "?") for c in chunks})
        # ↑ note : ces sources ne couvrent que le volet "produit" — le volet
        #   "stock" n'a pas de "source" au même sens, c'est un calcul,
        #   pas une recherche documentaire (limite à documenter aussi)

        return ChatResponse(answer=answer_text, sources=sources)

    except Exception as exc:
        logger.error("Erreur lors du traitement de la question : %s", exc)
        raise HTTPException(status_code=500, detail="Erreur interne lors du traitement.")


@router.get("/health")
def health() -> dict:
    """Endpoint de vérification — confirme que l'API est vivante."""
    return {"status": "ok"}