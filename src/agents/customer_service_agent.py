"""
Agent service client — RAG complet.

Assemble retrieval.py (recherche des chunks pertinents) et un LLM
(Ollama ou Groq, via get_llm) pour générer une réponse en langage
naturel, avec citation systématique de la source.

Le contexte est filtré AVANT d'être envoyé au LLM : on ne garde que les
produits qui ont une vraie correspondance avec la question. Retourne un
tuple (réponse, sources) pour que l'API affiche des tags cohérents avec
le texte généré, plutôt qu'une recherche séparée non filtrée.
"""

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from src.utils.llm import get_llm

from src.rag.retrieval import search
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROMPT_TEMPLATE = """Tu es un employé de supermarché sympathique et efficace, qui répond
directement aux clients — pas un assistant formel.

RÈGLES IMPORTANTES :
1. Ne mentionne QUE les produits qui correspondent EXACTEMENT à ce que le
   client demande.
2. Chaque produit ne doit apparaître qu'UNE SEULE FOIS dans ta réponse.
3. Si le client précise une variante précise (normale, classique, nature,
   zéro, light, sans sucre, sans gluten...), ne présente QUE le ou les
   produits qui correspondent à CETTE variante exacte — ignore les autres
   variantes du même produit même si elles sont dans le contexte. Exemple :
   si le client demande "coca normal" et que le contexte contient
   "Coca-Cola", "Coca-Cola Zero" et "Coca-Cola Lemon", ne mentionne QUE
   "Coca-Cola" (la version classique), pas les deux autres.
4. Réponds comme un vrai humain parlerait à un client — direct, naturel,
   sans formules robotiques. Une liste courte et claire suffit.
5. Si VRAIMENT aucun produit du contexte ne correspond, dis-le en une
   phrase courte ("Désolé, on n'en a pas en ce moment").
6. Cite la marque entre parenthèses APRÈS le nom du produit, sans répéter
   le nom du produit dans la parenthèse. Exemple correct :
   "On a le Skyr nature 0% (Yoplait)". Exemple INCORRECT à éviter :
   "On a le Skyr nature 0% (Skyr nature 0%, Yoplait)".
7. Commence ta réponse par une salutation courte et chaleureuse, adaptée
   à la langue du client — reste bref, 2-3 mots suffisent.
8. Réponds dans la MÊME langue/registre que la question du client.

Contexte :
{context}

Question du client : {question}

Réponse (salutation courte + réponse naturelle, directe, sans répétition, sans hors-sujet) :"""

STOPWORDS = {
    "les", "des", "qui", "que", "a", "de", "le", "la", "un", "une", "et",
    "avez", "vous", "il", "y", "ya", "til", "je", "cherche", "produits",
    "produit", "avoir",
}


def extract_keywords(text: str) -> set[str]:
    """Extrait les mots significatifs d'un texte, réduits à leur racine
    approximative (on retire les 's' finaux) pour matcher singulier/pluriel."""
    words = set()
    for w in text.split():
        clean = w.lower().strip("?,.!():")
        if len(clean) > 2 and clean not in STOPWORDS:
            words.add(clean.rstrip("s"))
    return words


def format_context(chunks: list[Document], question: str) -> str:
    """Assemble les chunks pertinents en texte de contexte.

    Filtres appliqués :
    1. Déduplication par nom de produit
    2. Exclusion des produits sans aucune correspondance avec la question
    """
    question_words = extract_keywords(question)

    seen_names = set()
    parts = []
    for chunk in chunks:
        name = chunk.metadata.get("product_name", "?")
        if name in seen_names:
            continue

        name_words = extract_keywords(name)
        content_words = extract_keywords(chunk.page_content)

        has_match = any(
            qw in name.lower() or qw in chunk.page_content.lower()
            for qw in question_words
        ) or bool(question_words & name_words) or bool(question_words & content_words)

        if not has_match:
            continue

        seen_names.add(name)
        brand = chunk.metadata.get("brand", "?")
        parts.append(f"[Produit : {name} — Marque : {brand}]\n{chunk.page_content}")

    return "\n\n".join(parts)


def answer_question(question: str) -> tuple[str, list[str]]:
    """Pipeline complet : retrieval, filtrage, génération.
    Retourne (réponse, liste des produits réellement utilisés)."""

    chunks = search(question)

    if not chunks:
        return "Je n'ai trouvé aucun produit correspondant à votre question.", []

    context = format_context(chunks, question)

    if not context:
        return "Désolé, je n'ai rien trouvé qui corresponde à votre demande.", []

    used_products = list({
        chunk.metadata.get("product_name", "?")
        for chunk in chunks
        if chunk.metadata.get("product_name", "?") in context
    })

    llm = get_llm(temperature=0.2, num_predict=350)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm
    response = chain.invoke({"context": context, "question": question})

    logger.info("Question : '%s' — %d produits utilisés", question, len(used_products))
    return response.content, used_products


if __name__ == "__main__":
    test_questions = [
        "Avez-vous des yaourts sans lactose ?",
        "Je cherche une boisson au cola",
        "Quels produits contiennent des cacahuètes ?",
    ]

    for q in test_questions:
        print(f"\n=== Question : {q} ===")
        answer, sources = answer_question(q)
        print(answer)
        print("Sources :", sources)