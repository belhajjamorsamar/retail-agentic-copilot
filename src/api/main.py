"""
Point d'entrée de l'API FastAPI.

Lancement : uvicorn src.api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router

app = FastAPI(title="retail-agentic-copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    # ↑ autorise UNIQUEMENT le frontend Next.js (qui tournera sur le port 3000)
    #   à appeler cette API — sécurité de base, pas n'importe quel site
    #   ne peut pas appeler notre API depuis un navigateur
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)