"""
Agent service client — RAG complet.

Assemble retrieval.py (recherche des chunks pertinents) et un LLM local
(Ollama) pour générer une réponse en langage naturel, avec citation
systématique de la source (nom du produit, marque).
"""

from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from src.utils.llm import get_llm


from src.rag.retrieval import search
from src.utils.logger import get_logger
from config import LLM_MODEL

logger = get_logger(__name__)

PROMPT_TEMPLATE = """Tu es un assistant service client pour un supermarché.
Réponds à la question du client en te basant UNIQUEMENT sur le contexte
fourni ci-dessous. Si le contexte ne contient pas assez d'information pour
répondre, dis-le clairement plutôt que d'inventer une réponse.

Pour chaque information que tu donnes, cite le nom du produit et sa marque
entre parenthèses, par exemple : (Skyr nature 0%, Yoplait).

Contexte :
{context}

Question du client : {question}

Réponse :"""


def format_context(chunks: list[Document]) -> str:
    """Assemble les chunks trouvés en un texte de contexte pour le prompt."""
    parts = []
    for chunk in chunks:
        name = chunk.metadata.get("product_name", "?")
        brand = chunk.metadata.get("brand", "?")
        parts.append(f"[Produit : {name} — Marque : {brand}]\n{chunk.page_content}")
    return "\n\n".join(parts)


def answer_question(question: str) -> str:
    """Pipeline complet : retrieval, puis génération de la réponse."""

    chunks = search(question)
    # ↑ réutilise retrieval.py — trouve les chunks pertinents (MMR)

    if not chunks:
        return "Je n'ai trouvé aucun produit correspondant à votre question."

    context = format_context(chunks)

    #llm = ChatOllama(model=LLM_MODEL, temperature=0.2)
    llm = get_llm(temperature=0.2, num_predict=350)
    # ↑ temperature basse = réponses plus factuelles, moins "créatives"
    #   important pour un service client qui ne doit pas inventer

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm
    # ↑ le symbole "|" (pipe) connecte le prompt au LLM : LangChain
    #   Expression Language (LCEL) — le prompt formaté est envoyé
    #   directement au LLM, comme un tuyau

    response = chain.invoke({"context": context, "question": question})

    logger.info("Question : '%s' — %d chunks utilisés", question, len(chunks))
    return response.content


if __name__ == "__main__":
    test_questions = [
        "Avez-vous des yaourts sans lactose ?",
        "Je cherche une boisson au cola",
        "Quels produits contiennent des cacahuètes ?",
    ]

    for q in test_questions:
        print(f"\n=== Question : {q} ===")
        print(answer_question(q))