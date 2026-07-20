"""
Point central de création du LLM — permet de basculer entre Ollama (local,
gratuit, mais lent sur CPU) et Groq (cloud, gratuit, beaucoup plus rapide)
via UN SEUL paramètre dans config.py (LLM_PROVIDER), sans toucher au reste
du code des agents.

Rien de l'ancien fonctionnement local n'est supprimé — juste rendu
interchangeable.
"""

from langchain_ollama import ChatOllama
from config import LLM_PROVIDER, LLM_MODEL, GROQ_MODEL, GROQ_API_KEY


def get_llm(temperature: float = 0.2, num_predict: int = 400):
    """Retourne le bon LLM selon LLM_PROVIDER, avec les mêmes paramètres
    de comportement (temperature, longueur max) quel que soit le fournisseur."""

    if LLM_PROVIDER == "groq":
        # ↓ NOUVEAU : Groq, cloud, rapide (LPU), gratuit sans carte,
        #   mais nécessite une connexion Internet stable
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=temperature,
            max_tokens=num_predict,
            # ↑ Groq utilise "max_tokens", Ollama utilise "num_predict" —
            #   même concept (limite de longueur de réponse), nom différent
        )

    # ↓ ANCIEN / PAR DÉFAUT : Ollama, 100% local, gratuit, tourne sur ta
    #   machine, aucune dépendance réseau — c'est ce qui fonctionnait
    #   depuis le début du projet, on ne le touche pas
    return ChatOllama(
        model=LLM_MODEL,
        temperature=temperature,
        num_predict=num_predict,
    )