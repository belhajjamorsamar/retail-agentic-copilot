"""
Superviseur — construit avec LangGraph : un graphe d'états explicite,
avec des nœuds (agents) et des routes conditionnelles entre eux, plutôt
qu'un simple enchaînement de if/else en Python.
"""

from typing import TypedDict, Optional

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

from src.agents.customer_service_agent import answer_question
from src.agents.pricing_agent_tool import check_products_at_risk
from src.utils.logger import get_logger
from config import LLM_MODEL, MAX_AGENT_ITERATIONS

logger = get_logger(__name__)


class AgentState(TypedDict):
    """L'état partagé qui circule entre les nœuds du graphe."""
    user_message: str
    needs_product: bool
    needs_stock: bool
    product_response: Optional[str]
    stock_response: Optional[str]
    final_response: Optional[str]


def classify_node(state: AgentState) -> dict:
    """Nœud 1 : détermine quels agents sont nécessaires."""
    llm = ChatOllama(model=LLM_MODEL, temperature=0.0)
    prompt = (
        "Réponds UNIQUEMENT au format suivant, sans autre texte :\n"
        "PRODUIT: oui/non\n"
        "STOCK: oui/non\n\n"
        "PRODUIT=oui si la question porte sur un produit, ses ingrédients, "
        "allergènes, marque, ou disponibilité.\n"
        "STOCK=oui si la question porte sur les dates de péremption, le "
        "gaspillage, les promotions liées au stock.\n"
        "Les deux peuvent être 'oui' en même temps.\n\n"
        f"Question : {state['user_message']}"
    )
    result = llm.invoke(prompt).content.lower()
    needs_product = "produit: oui" in result
    needs_stock = "stock: oui" in result

    if not needs_product and not needs_stock:
        needs_product = True  # garde-fou par défaut

    logger.info("Classification : produit=%s, stock=%s", needs_product, needs_stock)
    return {"needs_product": needs_product, "needs_stock": needs_stock}


def product_node(state: AgentState) -> dict:
    """Nœud 2a : appelle l'agent service client (RAG)."""
    logger.info("Nœud produit activé")
    return {"product_response": answer_question(state["user_message"])}


def stock_node(state: AgentState) -> dict:
    """Nœud 2b : appelle l'agent anti-gaspillage."""
    logger.info("Nœud stock activé")
    stock_info = check_products_at_risk.invoke({})
    llm = ChatOllama(model=LLM_MODEL, temperature=0.2)
    summary = llm.invoke(f"Résume en français cette liste de produits à risque :\n{stock_info}")
    return {"stock_response": summary.content}


def combine_node(state: AgentState) -> dict:
    """Nœud 3 : fusionne les réponses des agents activés en une seule réponse."""
    parts = [r for r in [state.get("product_response"), state.get("stock_response")] if r]

    if not parts:
        return {"final_response": "Je n'ai pas compris votre demande."}

    if len(parts) == 1:
        return {"final_response": parts[0]}

    llm = ChatOllama(model=LLM_MODEL, temperature=0.2)
    combined = llm.invoke(
        "Combine ces deux réponses en une seule réponse cohérente et "
        "naturelle, en français :\n\n" + "\n\n---\n\n".join(parts)
    )
    return {"final_response": combined.content}


def route_after_classify(state: AgentState) -> list[str]:
    """Décide vers quel(s) nœud(s) router après la classification."""
    destinations = []
    if state["needs_product"]:
        destinations.append("product_node")
    if state["needs_stock"]:
        destinations.append("stock_node")
    return destinations or ["combine_node"]


# --- Construction du graphe ---
graph = StateGraph(AgentState)
graph.add_node("classify", classify_node)
graph.add_node("product_node", product_node)
graph.add_node("stock_node", stock_node)
graph.add_node("combine_node", combine_node)

graph.set_entry_point("classify")
graph.add_conditional_edges(
    "classify", route_after_classify, ["product_node", "stock_node", "combine_node"]
)
graph.add_edge("product_node", "combine_node")
graph.add_edge("stock_node", "combine_node")
graph.add_edge("combine_node", END)

app = graph.compile()


def run_supervisor(user_message: str) -> str:
    """Point d'entrée : exécute le graphe complet pour une question donnée."""
    result = app.invoke(
        {"user_message": user_message, "needs_product": False, "needs_stock": False,
         "product_response": None, "stock_response": None, "final_response": None},
        config={"recursion_limit": MAX_AGENT_ITERATIONS},
        # ↑ notre garde-fou anti-boucle-infinie, réservé depuis le début du projet,
        #   enfin utilisé concrètement ici
    )
    return result["final_response"]


if __name__ == "__main__":
    test_questions = [
        "Avez-vous des yaourts sans lactose ?",
        "Quels produits sont proches de la péremption ?",
        "Vous avez des yaourts en promo ?",
    ]
    for q in test_questions:
        print(f"\n=== {q} ===")
        print(run_supervisor(q))