"""
Version agentique de l'agent anti-gaspillage.

Contrairement à pricing_agent.py (calcul déterministe pur), ce fichier
donne à un LLM la capacité de déclencher get_products_needing_attention()
selon le sens de la question posée.

Note d'architecture : on utilise une classification explicite en 2 étapes
(oui/non) plutôt que bind_tools() classique — un petit modèle local comme
llama3.2 s'est montré peu fiable pour décider seul d'appeler un outil
(il l'appelait même pour des questions sans rapport, comme "quelle est la
capitale de la France ?"). Une classification fermée est une tâche plus
simple et donc plus robuste pour ce modèle.
"""

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from src.utils.llm import get_llm


from src.agents.pricing_agent import get_products_needing_attention
from src.utils.logger import get_logger
from config import LLM_MODEL

logger = get_logger(__name__)


@tool
def check_products_at_risk() -> str:
    """Vérifie les produits du stock proches de la péremption et retourne
    les décisions de réduction de prix (automatiques ou en attente de
    validation humaine). Utilise cet outil quand on te demande l'état du
    stock, les produits à risque, ou les promotions liées au gaspillage."""

    decisions = get_products_needing_attention()

    if not decisions:
        return "Aucun produit ne nécessite d'attention actuellement."

    lines = []
    for d in decisions:
        status = "VALIDATION HUMAINE REQUISE" if d["requires_human_review"] else "réduction automatique"
        lines.append(
            f"- {d['product_name']} (J-{d['days_until_expiry']}) : "
            f"-{d['discount_percent']}% [{status}]"
        )
    return "\n".join(lines)


def is_stock_related(user_message: str, llm: ChatOllama) -> bool:
    """Demande au LLM une classification simple oui/non, plus fiable que
    le tool calling implicite pour un petit modèle comme llama3.2."""

    classification_prompt = (
        "Réponds UNIQUEMENT par 'oui' ou 'non', sans explication.\n"
        "Cette question concerne-t-elle le stock, les dates de péremption, "
        "le gaspillage alimentaire, ou des promotions liées au stock d'un "
        "supermarché ?\n\n"
        f"Question : {user_message}"
    )
    result = llm.invoke(classification_prompt).content.strip().lower()
    return "oui" in result


def run_pricing_agent(user_message: str) -> str:
    """Classification explicite d'abord, puis appel conditionnel de l'outil."""

    #llm = ChatOllama(model=LLM_MODEL, temperature=0.0)
    llm = get_llm(temperature=0.0, num_predict=30)


    if is_stock_related(user_message, llm):
        logger.info("Question classifiée comme liée au stock — appel de l'outil")
        tool_result = check_products_at_risk.invoke({})

        follow_up = llm.invoke(
            f"Question de l'utilisateur : {user_message}\n\n"
            f"Résultat de la vérification du stock :\n{tool_result}\n\n"
            f"Réponds à l'utilisateur en français, de façon claire et synthétique."
        )
        return follow_up.content
    else:
        logger.info("Question classifiée comme NON liée au stock — réponse directe")
        return llm.invoke(user_message).content


if __name__ == "__main__":
    test_messages = [
        "Y a-t-il des produits proches de la péremption ?",
        "Quelle est la capitale de la France ?",
    ]

    for msg in test_messages:
        print(f"\n=== {msg} ===")
        print(run_pricing_agent(msg))